/**
 * ============================================================================
 * Moteur d'Auto-complétion Contextuelle Avancée pour CodeMirror 6
 * ============================================================================
 *
 * Ce module fournit une source d'auto-complétion intelligente pour l'éditeur
 * de code Python de la calculatrice GeoNature (indicateurs de suivi).
 *
 * --- Architecture & Principes Fondamentaux ---
 *
 * 1. Découpage Hybride Frontend / Backend :
 *    - Le backend fournit à l'ouverture de la page un schéma JSON léger du contexte
 *      d'exécution (IndicatorExecutionContext) : tables de données réelles, colonnes
 *      spécifiques au protocole, tables de référence et fonctions de calcul autorisées.
 *    - Le frontend prend en charge en temps réel à 60 FPS (sans appel réseau) :
 *      * La navigation récursive dans les sous-objets (.values, .entity, .scope).
 *      * L'inférence de types des variables créées par l'utilisateur.
 *      * La détection des variables de boucles (for item in collection:) et compréhensions.
 *
 * 2. Modèle de Données et Grammaire Récursive GeoNature :
 *
 *    MonitoringCollection (observations, sites, visites)
 *      │
 *      └── PropertyCollection (ex: observations.cd_nom, sites.surface_zone)
 *            ├── .values ──────────> List[PropertyValue]
 *            │                         ├── .value  (valeur brute de la mesure)
 *            │                         └── .entity (Site, Visit, Observation)
 *            │                               └── Attributs scalaires (id, base_site_name...)
 *            ├── .scope  ──────────> Scope (Scope.SITE, Scope.VISIT, Scope.OBSERVATION, Scope.GLOBAL)
 *            └── .value  ──────────> float | int (valeur scalaire directe si agrégée)
 *
 * 3. Double Stratégie d'Analyse (AST Lezer + Regex de Secours) :
 *    Pendant qu'un utilisateur tape du code, la syntaxe Python est quasi-systématiquement
 *    incomplète ou invalide (parenthèse non fermée, mot tronqué, etc.).
 *    - L'AST Lezer (syntaxTree) fournit une analyse structurelle précise dès que le code est valide.
 *    - Des expressions régulières de secours (Unicode \p{L}) prennent le relais pour garantir
 *      que l'autocomplétion ne s'interrompt JAMAIS au cours de la frappe.
 * ============================================================================
 */

import { Completion, CompletionContext, CompletionResult } from '@codemirror/autocomplete';
import { syntaxTree } from '@codemirror/language';
import { ExecutionContextAttribute, IndicatorExecutionContext } from '../../interfaces';

// ============================================================================
// SECTION 1 : SCHÉMAS ET CONSTANTES DE TYPES DU DOMAINE GEONATURE
// ============================================================================

/**
 * Attributs et méthodes disponibles sur un objet de type PropertyCollection.
 * Représente une colonne de données (ex: observations.cd_nom, visites.visit_date_min)
 * ou le résultat d'une fonction de calcul GeoNature (gn_mean, gn_median, gn_extract).
 */
const PROPERTY_COLLECTION_ATTRIBUTES: ExecutionContextAttribute[] = [
  {
    name: 'values',
    type: 'List[PropertyValue]',
    description: 'Liste des valeurs mesurées ou calculées par entité (site ou visite)',
  },
  {
    name: 'scope',
    type: 'Scope',
    description: 'Niveau d agrégation des données (Scope.SITE, Scope.VISIT, Scope.OBSERVATION)',
  },
  {
    name: 'value',
    type: 'float | int',
    description: 'Valeur unique scalaire du calcul si applicable',
  },
];

/**
 * Attributs disponibles sur chaque élément d'une PropertyCollection (type PropertyValue).
 * Accessible par indexation (ex: observations.cd_nom.values[0]) ou par boucle (for prop in values:).
 */
const PROPERTY_VALUE_ATTRIBUTES: ExecutionContextAttribute[] = [
  {
    name: 'value',
    type: 'Any',
    description: 'Valeur de la mesure ou du résultat de calcul pour l entité',
  },
  {
    name: 'entity',
    type: 'Entity',
    description: 'Entité géographique (site) ou temporelle (visite) associée à la valeur',
  },
];

/**
 * Attributs disponibles sur un résultat de campagne de suivi (type CampaignResult).
 * Disponible dans les scopes 'overview' et 'statistical-tests' (ex: campaigns[0]).
 */
const CAMPAIGN_RESULT_ATTRIBUTES: ExecutionContextAttribute[] = [
  {
    name: 'start_date',
    type: 'datetime',
    description: 'Date de début de la campagne de suivi (ex: "2023-01-01")',
  },
  {
    name: 'end_date',
    type: 'datetime',
    description: 'Date de fin de la campagne de suivi (ex: "2023-12-31")',
  },
  {
    name: 'vars',
    type: 'CampaignVars',
    description: 'Conteneur des variables calculées lors de cette campagne (ex: vars.médiane)',
  },
];

// ============================================================================
// SECTION 2 : POINT D'ENTRÉE CODEMIRROR (Extension d'autocomplétion)
// ============================================================================

/**
 * Fabrique la fonction source de complétion contextuelle pour CodeMirror 6.
 *
 * @param getContext Fonction accesseur retournant le contexte d'exécution courant
 *                   (chargé depuis le backend ou le mock réactif).
 * @returns Une fonction de complétion CodeMirror (CompletionSource)
 */
export function createCodeEditorCompletionSource(getContext: () => IndicatorExecutionContext) {
  return (completionContext: CompletionContext): CompletionResult | null => {
    const executionContext = getContext();

    // Analyse préliminaire du document pour extraire les variables locales et les boucles
    const loopVariableMap = extractLoopVariables(completionContext);
    const localVariableTypeMap = extractLocalVariableTypes(completionContext, executionContext);

    // ------------------------------------------------------------------------
    // Mode A : Complétion après un point (Navigation d'attributs / sous-objets)
    // ------------------------------------------------------------------------
    // Détecte les expressions chaînées avant le curseur, par exemple :
    // - "observations.cd_nom." ➔ values, scope, value
    // - "observations.cd_nom.values[0]." ➔ value, entity
    // - "observations.cd_nom.values[0].entity." ➔ base_site_name, id_base_site...
    // - "campaigns[0]." ➔ start_date, end_date, vars
    // - "campaigns[0].vars.médiane." ➔ values, scope, value
    // - "moyenne." ➔ values, scope, value (inféré depuis moyenne = gn_mean(...))
    // - "campagne1." ➔ start_date, end_date, vars (inféré depuis campagne1 = campaigns[0])
    // - "prop." ➔ value, entity (inféré depuis for prop in moyenne.values:)
    // Supporte les caractères Unicode (\p{L}) pour les variables françaises (médiane, récolte...)
    const memberMatch = completionContext.matchBefore(
      /([\p{L}_][\p{L}\p{N}_]*(?:\[\s*\d+\s*\])?(?:\.[\p{L}_][\p{L}\p{N}_]*(?:\[\s*\d+\s*\])?)*)\.([\p{L}_][\p{L}\p{N}_]*)?$/u
    );

    if (memberMatch) {
      const fullMatchedText = memberMatch.text;
      const lastDotIndex = fullMatchedText.lastIndexOf('.');
      const pathExpression = fullMatchedText.substring(0, lastDotIndex);

      // Résolution récursive du type de l'expression située avant le point
      const targetAttributes = resolvePathAttributes(
        pathExpression,
        executionContext,
        loopVariableMap,
        localVariableTypeMap
      );

      if (targetAttributes && targetAttributes.length > 0) {
        const attributeOptions: Completion[] = targetAttributes.map((attribute) => ({
          label: attribute.name,
          type: 'property',
          detail: attribute.type,
          info: attribute.description,
          boost: 90, // Priorité haute pour les attributs membres directs
        }));

        return {
          from: memberMatch.from + lastDotIndex + 1,
          options: attributeOptions,
          validFor: /^[\p{L}\p{N}_]*$/u,
        };
      }
      return null;
    }

    // ------------------------------------------------------------------------
    // Mode B : Complétion de mots et symboles racine (ex: "obs", "gn_", "med")
    // ------------------------------------------------------------------------
    const wordMatch = completionContext.matchBefore(/[\p{L}_][\p{L}\p{N}_]*$/u);
    if (!wordMatch && !completionContext.explicit) {
      return null;
    }

    // 1. Objets racines du contexte (observations, sites, visites, campaigns, Scope, ReferenceTable...)
    const objectOptions: Completion[] = Object.values(executionContext.objects).map(
      (contextObject) => ({
        label: contextObject.name,
        type: 'variable',
        detail: contextObject.type,
        info: contextObject.description,
        boost: 60,
      })
    );

    // 2. Fonctions utilitaires et de calcul (gn_mean, gn_median, gn_extract, len, round...)
    const functionOptions: Completion[] = executionContext.functions.map((contextFunction) => ({
      label: contextFunction.name,
      type: 'function',
      detail: contextFunction.signature,
      info: contextFunction.description,
      boost: 50,
    }));

    // 3. Variables et fonctions locales définies directement par l'utilisateur
    const localUserSymbols = extractLocalUserSymbols(completionContext);

    return {
      from: wordMatch ? wordMatch.from : completionContext.pos,
      options: [...objectOptions, ...functionOptions, ...localUserSymbols],
      validFor: /^[\p{L}\p{N}_]*$/u,
    };
  };
}

// ============================================================================
// SECTION 3 : RÉSOLUTION RÉCURSIVE DE CHEMIN (Path Resolver)
// ============================================================================

/**
 * Résout récursivement les attributs d'un chemin d'accès complexe composé
 * d'identifiants, d'opérateurs de chaînage '.' et d'indexations '[0]'.
 *
 * Fonctionnement par automate à états finis :
 * 1. Résout le type du segment racine (ex: 'observations', 'campaigns[0]', 'moyenne').
 * 2. Fait évoluer le type courant à chaque segment successif selon les règles métier GeoNature.
 * 3. Retourne la liste des attributs correspondant au type final atteint.
 *
 * @param pathExpression Expression à analyser (ex: "observations.cd_nom.values[0].entity")
 * @param executionContext Métadonnées globales fournies par le backend
 * @param loopVariableMap Table des correspondances des variables de boucle
 * @param localVariableTypeMap Table des types inférés pour les variables locales
 * @returns Liste des attributs disponibles sur le dernier niveau ou null si inconnu
 */
function resolvePathAttributes(
  pathExpression: string,
  executionContext: IndicatorExecutionContext,
  loopVariableMap: Map<string, string>,
  localVariableTypeMap: Map<string, string>
): ExecutionContextAttribute[] | null {
  const pathSegments = pathExpression.split('.');
  if (pathSegments.length === 0) {
    return null;
  }

  let currentType: string | null = null;
  let customAttributes: ExecutionContextAttribute[] | null = null;

  // 1. Résolution du premier segment (racine de l'expression)
  const rootSegment = pathSegments[0].trim();
  const rootIndexMatch = rootSegment.match(/^([\p{L}_][\p{L}\p{N}_]*)\[\s*(\d+)\s*\]$/u);
  const rootIdentifier = rootIndexMatch ? rootIndexMatch[1] : rootSegment;
  const isRootIndexed = Boolean(rootIndexMatch);

  if (loopVariableMap.has(rootIdentifier)) {
    // Cas d'une variable de boucle (ex: for prop in moyenne.values:)
    const parentIterable = loopVariableMap.get(rootIdentifier) || '';
    if (parentIterable.endsWith('.values')) {
      currentType = 'PropertyValue';
    } else if (parentIterable === 'campaigns') {
      currentType = 'CampaignResult';
    } else if (
      parentIterable === 'sites' ||
      parentIterable === 'visites' ||
      parentIterable === 'observations'
    ) {
      currentType = 'Entity';
    } else {
      currentType = 'PropertyValue';
    }
  } else if (localVariableTypeMap.has(rootIdentifier)) {
    // Cas d'une variable utilisateur typée par inférence locale
    currentType = localVariableTypeMap.get(rootIdentifier) || null;
  } else if (rootIdentifier === 'campaigns') {
    // Cas de la collection globale campaigns
    currentType = isRootIndexed ? 'CampaignResult' : 'CampaignsList';
  } else if (executionContext.objects[rootIdentifier]) {
    // Cas d'un objet racine injecté par le backend (observations, sites, Scope, ReferenceTable...)
    const targetRootObject = executionContext.objects[rootIdentifier];
    if (
      rootIdentifier === 'observations' ||
      rootIdentifier === 'sites' ||
      rootIdentifier === 'visites'
    ) {
      currentType = isRootIndexed ? 'Entity' : 'MonitoringCollection';
    } else {
      currentType = isRootIndexed ? 'IndexedObject' : 'GenericObject';
      customAttributes = isRootIndexed
        ? targetRootObject.itemAttributes || targetRootObject.attributes
        : targetRootObject.attributes;
    }
  }

  if (!currentType) {
    return null;
  }

  // 2. Navigation récursive à travers les segments suivants
  for (let segmentIndex = 1; segmentIndex < pathSegments.length; segmentIndex++) {
    const segmentText = pathSegments[segmentIndex].trim();
    const segmentIndexMatch = segmentText.match(/^([\p{L}_][\p{L}\p{N}_]*)\[\s*(\d+)\s*\]$/u);
    const segmentIdentifier = segmentIndexMatch ? segmentIndexMatch[1] : segmentText;
    const isSegmentIndexed = Boolean(segmentIndexMatch);

    if (currentType === 'MonitoringCollection') {
      // Une colonne de données (ex: observations.cd_nom) est une PropertyCollection
      currentType = isSegmentIndexed ? 'PropertyValue' : 'PropertyCollection';
    } else if (currentType === 'CampaignResult') {
      if (segmentIdentifier === 'vars') {
        currentType = 'CampaignVars';
      } else {
        currentType = 'primitive';
      }
    } else if (currentType === 'CampaignVars') {
      // Chaque variable de campagne dans vars (ex: vars.médiane) est une PropertyCollection
      currentType = isSegmentIndexed ? 'PropertyValue' : 'PropertyCollection';
    } else if (currentType === 'PropertyCollection') {
      if (segmentIdentifier === 'values') {
        currentType = isSegmentIndexed ? 'PropertyValue' : 'ValuesList';
      } else if (segmentIdentifier === 'scope' || segmentIdentifier === 'value') {
        currentType = 'primitive';
      }
    } else if (currentType === 'ValuesList') {
      if (isSegmentIndexed) {
        currentType = 'PropertyValue';
      }
    } else if (currentType === 'PropertyValue') {
      if (segmentIdentifier === 'entity') {
        currentType = 'Entity';
      } else if (segmentIdentifier === 'value') {
        currentType = 'primitive';
      }
    } else if (currentType === 'Entity') {
      currentType = 'primitive';
    }
  }

  // 3. Fourniture des attributs correspondant au type résolu
  return resolveAttributesForType(currentType, executionContext, customAttributes);
}

/**
 * Associe un type d'objet résolu à sa liste d'attributs de complétion.
 *
 * @param targetType Type résolu par la traversée (ex: 'PropertyCollection', 'Entity')
 * @param executionContext Contexte d'exécution global
 * @param customAttributes Attributs spécifiques d'un objet racine si applicable
 * @returns Liste d'attributs de complétion ou null si type primitif/inconnu
 */
function resolveAttributesForType(
  targetType: string | null,
  executionContext: IndicatorExecutionContext,
  customAttributes: ExecutionContextAttribute[] | null
): ExecutionContextAttribute[] | null {
  if (!targetType || targetType === 'primitive') {
    return null;
  }

  if (targetType === 'PropertyCollection') {
    return PROPERTY_COLLECTION_ATTRIBUTES;
  }

  if (targetType === 'PropertyValue') {
    return PROPERTY_VALUE_ATTRIBUTES;
  }

  if (targetType === 'Entity') {
    return getEntityAttributes(executionContext);
  }

  if (targetType === 'CampaignResult') {
    return CAMPAIGN_RESULT_ATTRIBUTES;
  }

  if (targetType === 'CampaignVars') {
    return getCampaignVariablesAttributes(executionContext);
  }

  if (targetType === 'MonitoringCollection') {
    return customAttributes;
  }

  return customAttributes;
}

/**
 * Récupère l'ensemble des attributs scalaires d'entité (champs de sites et de visites,
 * incluant les colonnes dynamiques spécifiques au protocole).
 * Utilisé sur la complétion de '.entity.' (ex: observations.cd_nom.values[0].entity.).
 */
function getEntityAttributes(
  executionContext: IndicatorExecutionContext
): ExecutionContextAttribute[] {
  const entityAttributeMap = new Map<string, ExecutionContextAttribute>();

  // Attributs issus des sites (identifiants, nom usuel, surface, etc.)
  const siteObject = executionContext.objects['sites'];
  const siteAttributes = siteObject?.itemAttributes || siteObject?.attributes;
  if (siteAttributes) {
    for (const siteAttribute of siteAttributes) {
      entityAttributeMap.set(siteAttribute.name, {
        name: siteAttribute.name,
        type: siteAttribute.type === 'PropertyCollection' ? 'valeur' : siteAttribute.type,
        description: siteAttribute.description,
      });
    }
  }

  // Attributs issus des visites (date, durée, météo, etc.)
  const visitObject = executionContext.objects['visites'];
  const visitAttributes = visitObject?.itemAttributes || visitObject?.attributes;
  if (visitAttributes) {
    for (const visitAttribute of visitAttributes) {
      if (!entityAttributeMap.has(visitAttribute.name)) {
        entityAttributeMap.set(visitAttribute.name, {
          name: visitAttribute.name,
          type: visitAttribute.type === 'PropertyCollection' ? 'valeur' : visitAttribute.type,
          description: visitAttribute.description,
        });
      }
    }
  }

  return Array.from(entityAttributeMap.values());
}

/**
 * Récupère les attributs de variables calculées pour l'objet de synthèse 'vars' (CampaignVars).
 * Utilisé pour compléter 'campaigns[0].vars.' ou 'campaign.vars.'.
 */
function getCampaignVariablesAttributes(
  executionContext: IndicatorExecutionContext
): ExecutionContextAttribute[] {
  const campaignsObject = executionContext.objects['campaigns'];
  if (campaignsObject?.nestedObjects?.['vars']?.attributes) {
    return campaignsObject.nestedObjects['vars'].attributes;
  }

  const defaultVariables = ['médiane', 'moyenne', 'score_global', 'indice_abondance'];
  return defaultVariables.map((variableName) => ({
    name: variableName,
    type: 'PropertyCollection',
    description: `Variable calculée "${variableName}" pour la campagne`,
  }));
}

// ============================================================================
// SECTION 4 : INFÉRENCE DE TYPES LOCAUX (AST Lezer + Regex de secours)
// ============================================================================

/**
 * Analyse le document en cours d'édition pour déduire le type des variables créées
 * par l'utilisateur via assignation Python :
 * - Fonctions de calcul : moyenne = gn_mean(...) ➔ PropertyCollection
 * - Assignations d'attributs : cd = observations.cd_nom ➔ PropertyCollection
 * - Indexations de campagnes : campagne1 = campaigns[0] ➔ CampaignResult
 * - Assignations d'éléments de valeurs : premier = moyenne.values[0] ➔ PropertyValue
 * - Assignations d'entités : ent = premier.entity ➔ Entity
 *
 * Utilise l'AST Lezer de CodeMirror complété par des expressions régulières pour
 * maintenir l'inférence même quand le code est temporairement invalide pendant la frappe.
 *
 * @param completionContext Contexte de l'éditeur CodeMirror
 * @param executionContext Métadonnées du contexte d'exécution
 * @returns Map associant le nom de chaque variable locale à son type déduit
 */
function extractLocalVariableTypes(
  completionContext: CompletionContext,
  executionContext: IndicatorExecutionContext
): Map<string, string> {
  const localVariableTypeMap = new Map<string, string>();
  const documentText = completionContext.state.doc.toString();
  const tree = syntaxTree(completionContext.state);

  // Construction d'une table de correspondance des fonctions et de leur type de retour
  const functionReturnTypeMap = new Map<string, string>();
  for (const executionFunction of executionContext.functions) {
    if (executionFunction.returnType) {
      functionReturnTypeMap.set(executionFunction.name, executionFunction.returnType);
    }
  }

  // 1. Analyse structurelle via l'AST Lezer
  try {
    tree.iterate({
      enter: (nodeSnapshot) => {
        if (nodeSnapshot.name === 'AssignStatement') {
          const cursor = nodeSnapshot.node.cursor();
          let assignedVariableName = '';
          let assignedType: string | null = null;

          if (cursor.firstChild()) {
            do {
              if (cursor.name === 'VariableName' && !assignedVariableName) {
                // Partie gauche (LHS) : nom de la variable assignée
                assignedVariableName = documentText.slice(cursor.from, cursor.to);
              } else if (cursor.name === 'CallExpression') {
                // Partie droite (RHS) : appel de fonction (ex: moyenne = gn_mean(...))
                const callText = documentText.slice(cursor.from, cursor.to);
                const callMatch = callText.match(/^([a-zA-Z_]\w*)\s*\(/);
                if (callMatch) {
                  const functionName = callMatch[1];
                  if (functionReturnTypeMap.has(functionName)) {
                    assignedType = functionReturnTypeMap.get(functionName) || null;
                  } else if (
                    functionName.startsWith('gn_mean') ||
                    functionName.startsWith('gn_median') ||
                    functionName.startsWith('gn_extract') ||
                    functionName.startsWith('create_abondance_perc')
                  ) {
                    assignedType = 'PropertyCollection';
                  }
                }
              } else if (cursor.name === 'MemberExpression') {
                // Partie droite (RHS) : accès membre ou indexation (ex: cd = obs.cd_nom, c1 = campaigns[0])
                const memberText = documentText.slice(cursor.from, cursor.to);
                if (
                  memberText.startsWith('observations.') ||
                  memberText.startsWith('sites.') ||
                  memberText.startsWith('visites.') ||
                  memberText.includes('.vars.')
                ) {
                  assignedType = 'PropertyCollection';
                } else if (
                  memberText.startsWith('campaigns[') ||
                  memberText.includes('campaigns[')
                ) {
                  assignedType = 'CampaignResult';
                } else if (memberText.endsWith('.values[0]') || memberText.includes('.values[')) {
                  assignedType = 'PropertyValue';
                } else if (memberText.endsWith('.entity')) {
                  assignedType = 'Entity';
                }
              }
            } while (cursor.nextSibling());
          }

          if (assignedVariableName && assignedType) {
            localVariableTypeMap.set(assignedVariableName, assignedType);
          }
        }
      },
    });
  } catch (treeError) {
    console.debug('Erreur AST assignations locales', treeError);
  }

  // 2. Expressions régulières de secours (indispensables pendant la saisie de code incomplet)
  const calculationPattern =
    /^\s*([\p{L}_][\p{L}\p{N}_]*)\s*=\s*(gn_mean|gn_median|gn_extract|create_abondance_perc)\b/gmu;
  let calculationMatch = calculationPattern.exec(documentText);
  while (calculationMatch !== null) {
    const variableName = calculationMatch[1];
    if (variableName && !localVariableTypeMap.has(variableName)) {
      localVariableTypeMap.set(variableName, 'PropertyCollection');
    }
    calculationMatch = calculationPattern.exec(documentText);
  }

  const memberAssignPattern =
    /^\s*([\p{L}_][\p{L}\p{N}_]*)\s*=\s*(observations|sites|visites)\.([\p{L}_][\p{L}\p{N}_]*)/gmu;
  let memberAssignMatch = memberAssignPattern.exec(documentText);
  while (memberAssignMatch !== null) {
    const variableName = memberAssignMatch[1];
    if (variableName && !localVariableTypeMap.has(variableName)) {
      localVariableTypeMap.set(variableName, 'PropertyCollection');
    }
    memberAssignMatch = memberAssignPattern.exec(documentText);
  }

  const campaignIndexPattern = /^\s*([\p{L}_][\p{L}\p{N}_]*)\s*=\s*campaigns\[\s*\d+\s*\]/gmu;
  let campaignIndexMatch = campaignIndexPattern.exec(documentText);
  while (campaignIndexMatch !== null) {
    const variableName = campaignIndexMatch[1];
    if (variableName && !localVariableTypeMap.has(variableName)) {
      localVariableTypeMap.set(variableName, 'CampaignResult');
    }
    campaignIndexMatch = campaignIndexPattern.exec(documentText);
  }

  const valueIndexAssignPattern =
    /^\s*([\p{L}_][\p{L}\p{N}_]*)\s*=\s*[\p{L}_][\p{L}\p{N}_]*(?:\.[\p{L}_][\p{L}\p{N}_]*)*\.values\[\s*\d+\s*\]/gmu;
  let valueIndexMatch = valueIndexAssignPattern.exec(documentText);
  while (valueIndexMatch !== null) {
    const variableName = valueIndexMatch[1];
    if (variableName && !localVariableTypeMap.has(variableName)) {
      localVariableTypeMap.set(variableName, 'PropertyValue');
    }
    valueIndexMatch = valueIndexAssignPattern.exec(documentText);
  }

  const entityAssignPattern =
    /^\s*([\p{L}_][\p{L}\p{N}_]*)\s*=\s*[\p{L}_][\p{L}\p{N}_]*(?:\.[\p{L}_][\p{L}\p{N}_]*)*\.entity\b/gmu;
  let entityAssignMatch = entityAssignPattern.exec(documentText);
  while (entityAssignMatch !== null) {
    const variableName = entityAssignMatch[1];
    if (variableName && !localVariableTypeMap.has(variableName)) {
      localVariableTypeMap.set(variableName, 'Entity');
    }
    entityAssignMatch = entityAssignPattern.exec(documentText);
  }

  return localVariableTypeMap;
}

// ============================================================================
// SECTION 5 : EXTRACTION DES BOUCLES ET COMPRÉHENSIONS (Loop & Comprehension Tracker)
// ============================================================================

/**
 * Extrait les correspondances des boucles 'for <item> in <collection>:'
 * ainsi que des compréhensions de listes '[... for <item> in <collection>]'.
 * Permet d'associer la variable d'itération à sa collection parente (ex: 'prop' ➔ 'moyenne.values').
 *
 * @param completionContext Contexte de l'éditeur CodeMirror
 * @returns Map associant le nom de la variable d'itération à l'expression itérable
 */
function extractLoopVariables(completionContext: CompletionContext): Map<string, string> {
  const loopVariableMap = new Map<string, string>();
  const documentText = completionContext.state.doc.toString();
  const tree = syntaxTree(completionContext.state);

  // 1. Analyse via l'AST Lezer
  try {
    tree.iterate({
      enter: (nodeSnapshot) => {
        if (
          nodeSnapshot.name === 'ForStatement' ||
          nodeSnapshot.name === 'ArrayComprehensionExpression'
        ) {
          const cursor = nodeSnapshot.node.cursor();
          let loopVariableName = '';
          let iterableExpression = '';
          let hasFoundInKeyword = false;

          if (cursor.firstChild()) {
            do {
              if (cursor.name === 'VariableName' && !loopVariableName) {
                loopVariableName = documentText.slice(cursor.from, cursor.to);
              } else if (cursor.name === 'in') {
                hasFoundInKeyword = true;
              } else if (
                hasFoundInKeyword &&
                (cursor.name === 'VariableName' ||
                  cursor.name === 'MemberExpression' ||
                  cursor.name === 'ArrayExpression')
              ) {
                iterableExpression = documentText.slice(cursor.from, cursor.to);
                break;
              }
            } while (cursor.nextSibling());
          }

          if (loopVariableName && iterableExpression) {
            loopVariableMap.set(loopVariableName, iterableExpression);
          }
        }
      },
    });
  } catch (treeError) {
    console.debug('Erreur AST des boucles for', treeError);
  }

  // 2. Analyse complémentaire par regex (gérant for ... in ...: et [... for ... in ...])
  const loopPattern =
    /for\s+([\p{L}_][\p{L}\p{N}_]*)\s+in\s+([\p{L}_][\p{L}\p{N}_]*(?:\[\s*\d+\s*\])?(?:\.[\p{L}_][\p{L}\p{N}_]*(?:\[\s*\d+\s*\])?)*)/gu;
  let loopMatch = loopPattern.exec(documentText);
  while (loopMatch !== null) {
    const loopVariableName = loopMatch[1];
    const iterableExpression = loopMatch[2];
    if (loopVariableName && iterableExpression && !loopVariableMap.has(loopVariableName)) {
      loopVariableMap.set(loopVariableName, iterableExpression);
    }
    loopMatch = loopPattern.exec(documentText);
  }

  return loopVariableMap;
}

// ============================================================================
// SECTION 6 : EXTRACTION DES SYMBOLES UTILISATEUR (Variables & Fonctions locales)
// ============================================================================

/**
 * Extrait l'ensemble des symboles créés directement par l'utilisateur dans son code Python :
 * - Variables créées par assignation (ex: ma_variable = ...)
 * - Variables créées par boucle for ou compréhension de liste (ex: for campaign in ...)
 * - Fonctions locales créées par 'def' (ex: def calculer_score(...)
 *
 * Ces symboles sont proposés lors de la complétion racine avec une icône adaptée et un boost modéré.
 *
 * @param completionContext Contexte de l'éditeur CodeMirror
 * @returns Liste de propositions de complétion (Completion[])
 */
function extractLocalUserSymbols(completionContext: CompletionContext): Completion[] {
  const symbolMap = new Map<string, Completion>();
  const documentText = completionContext.state.doc.toString();
  const tree = syntaxTree(completionContext.state);

  // 1. Analyse via l'AST Lezer de CodeMirror
  try {
    tree.iterate({
      enter: (nodeSnapshot) => {
        // Détection des assignations : VariableName à l'intérieur d'un AssignStatement, ForStatement ou ArrayComprehensionExpression
        if (
          nodeSnapshot.name === 'VariableName' &&
          (nodeSnapshot.node.parent?.name === 'AssignStatement' ||
            nodeSnapshot.node.parent?.name === 'ForStatement' ||
            nodeSnapshot.node.parent?.name === 'ArrayComprehensionExpression')
        ) {
          const variableName = documentText.slice(nodeSnapshot.from, nodeSnapshot.to);
          if (variableName && !symbolMap.has(variableName)) {
            symbolMap.set(variableName, {
              label: variableName,
              type: 'variable',
              detail: 'Variable locale',
              boost: 30,
            });
          }
        }

        // Détection des définitions de fonctions : VariableName dans FunctionDefinition
        if (
          nodeSnapshot.name === 'VariableName' &&
          nodeSnapshot.node.parent?.name === 'FunctionDefinition'
        ) {
          const functionName = documentText.slice(nodeSnapshot.from, nodeSnapshot.to);
          if (functionName && !symbolMap.has(functionName)) {
            symbolMap.set(functionName, {
              label: functionName,
              type: 'function',
              detail: 'Fonction locale',
              boost: 35,
            });
          }
        }
      },
    });
  } catch (treeError) {
    console.debug('Erreur AST symboles locaux', treeError);
  }

  // 2. Complément d'analyse par regex pour une résilience maximale
  const assignmentPattern = /^\s*([\p{L}_][\p{L}\p{N}_]*)\s*=/gmu;
  let assignmentMatch = assignmentPattern.exec(documentText);
  while (assignmentMatch !== null) {
    const variableName = assignmentMatch[1];
    if (variableName && !symbolMap.has(variableName)) {
      symbolMap.set(variableName, {
        label: variableName,
        type: 'variable',
        detail: 'Variable locale',
        boost: 30,
      });
    }
    assignmentMatch = assignmentPattern.exec(documentText);
  }

  const loopPattern = /for\s+([\p{L}_][\p{L}\p{N}_]*)\s+in/gu;
  let loopMatch = loopPattern.exec(documentText);
  while (loopMatch !== null) {
    const variableName = loopMatch[1];
    if (variableName && !symbolMap.has(variableName)) {
      symbolMap.set(variableName, {
        label: variableName,
        type: 'variable',
        detail: 'Variable de boucle',
        boost: 35,
      });
    }
    loopMatch = loopPattern.exec(documentText);
  }

  const functionPattern = /^\s*def\s+([\p{L}_][\p{L}\p{N}_]*)\s*\(/gmu;
  let functionMatch = functionPattern.exec(documentText);
  while (functionMatch !== null) {
    const functionName = functionMatch[1];
    if (functionName && !symbolMap.has(functionName)) {
      symbolMap.set(functionName, {
        label: functionName,
        type: 'function',
        detail: 'Fonction locale',
        boost: 35,
      });
    }
    functionMatch = functionPattern.exec(documentText);
  }

  return Array.from(symbolMap.values());
}
