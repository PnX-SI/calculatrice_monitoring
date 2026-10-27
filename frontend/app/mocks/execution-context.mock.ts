import { IndicatorExecutionContext, ProtocolProperties } from '../interfaces';

export function getMockExecutionContext(
  protocolProperties?: ProtocolProperties,
  scope: string = 'campaign',
  campaignVariables: string[] = []
): IndicatorExecutionContext {
  const siteProtocolAttributes = (
    protocolProperties?.site || ['surface_zone', 'pente_moyenne']
  ).map((protocolPropertyName) => ({
    name: protocolPropertyName,
    type: 'PropertyCollection',
    description: `Propriété de site spécifique au protocole : ${protocolPropertyName}`,
  }));

  const visitProtocolAttributes = (
    protocolProperties?.visit || ['meteo', 'heure_debut', 'heure_fin']
  ).map((protocolPropertyName) => ({
    name: protocolPropertyName,
    type: 'PropertyCollection',
    description: `Propriété de visite spécifique au protocole : ${protocolPropertyName}`,
  }));

  const observationProtocolAttributes = (
    protocolProperties?.observation || ['cd_nom', 'nom_cite', 'abondance', 'stade_vie']
  ).map((protocolPropertyName) => ({
    name: protocolPropertyName,
    type: 'PropertyCollection',
    description: `Propriété d observation spécifique au protocole : ${protocolPropertyName}`,
  }));

  const sitesAttributes = [
    {
      name: 'id_base_site',
      type: 'PropertyCollection',
      description: 'Identifiant unique du site dans la base GeoNature',
    },
    {
      name: 'base_site_name',
      type: 'PropertyCollection',
      description: 'Nom ou libellé usuel du site',
    },
    {
      name: 'base_site_code',
      type: 'PropertyCollection',
      description: 'Code identifiant textuel du site',
    },
    ...siteProtocolAttributes,
  ];

  const siteItemAttributes = [
    {
      name: 'id_base_site',
      type: 'int',
      description: 'Identifiant unique du site dans la base GeoNature',
    },
    {
      name: 'base_site_name',
      type: 'string',
      description: 'Nom ou libellé usuel du site',
    },
    {
      name: 'base_site_code',
      type: 'string',
      description: 'Code identifiant textuel du site',
    },
    ...siteProtocolAttributes.map((attribute) => ({
      name: attribute.name,
      type: 'valeur',
      description: attribute.description,
    })),
  ];

  const visitsAttributes = [
    {
      name: 'id_base_visit',
      type: 'PropertyCollection',
      description: 'Identifiant unique de la visite de terrain',
    },
    {
      name: 'id_base_site',
      type: 'PropertyCollection',
      description: 'Identifiant du site visité',
    },
    {
      name: 'visit_date_min',
      type: 'PropertyCollection',
      description: 'Date de début de la visite de terrain',
    },
    {
      name: 'visit_date_max',
      type: 'PropertyCollection',
      description: 'Date de fin de la visite de terrain',
    },
    ...visitProtocolAttributes,
  ];

  const visitItemAttributes = [
    {
      name: 'id_base_visit',
      type: 'int',
      description: 'Identifiant unique de la visite de terrain',
    },
    {
      name: 'id_base_site',
      type: 'int',
      description: 'Identifiant du site visité',
    },
    {
      name: 'visit_date_min',
      type: 'datetime',
      description: 'Date de début de la visite de terrain',
    },
    {
      name: 'visit_date_max',
      type: 'datetime',
      description: 'Date de fin de la visite de terrain',
    },
    ...visitProtocolAttributes.map((attribute) => ({
      name: attribute.name,
      type: 'valeur',
      description: attribute.description,
    })),
  ];

  const observationsAttributes = [
    {
      name: 'id_observation',
      type: 'PropertyCollection',
      description: 'Identifiant unique de la donnée d observation',
    },
    {
      name: 'id_base_visit',
      type: 'PropertyCollection',
      description: 'Identifiant de la visite associée à l observation',
    },
    {
      name: 'id_base_site',
      type: 'PropertyCollection',
      description: 'Identifiant du site où a eu lieu l observation',
    },
    {
      name: 'cd_nom',
      type: 'PropertyCollection',
      description: 'Identifiant Taxref du taxon observé',
    },
    {
      name: 'nom_cite',
      type: 'PropertyCollection',
      description: 'Nom scientifique ou vernaculaire cité par l observateur',
    },
    {
      name: 'count_min',
      type: 'PropertyCollection',
      description: 'Effectif minimum observé',
    },
    {
      name: 'count_max',
      type: 'PropertyCollection',
      description: 'Effectif maximum observé',
    },
    ...observationProtocolAttributes,
  ];

  const observationItemAttributes = [
    {
      name: 'id_observation',
      type: 'int',
      description: 'Identifiant unique de la donnée d observation',
    },
    {
      name: 'id_base_visit',
      type: 'int',
      description: 'Identifiant de la visite associée à l observation',
    },
    {
      name: 'id_base_site',
      type: 'int',
      description: 'Identifiant du site où a eu lieu l observation',
    },
    {
      name: 'cd_nom',
      type: 'int',
      description: 'Identifiant Taxref du taxon observé',
    },
    {
      name: 'nom_cite',
      type: 'string',
      description: 'Nom scientifique ou vernaculaire cité par l observateur',
    },
    {
      name: 'count_min',
      type: 'int',
      description: 'Effectif minimum observé',
    },
    {
      name: 'count_max',
      type: 'int',
      description: 'Effectif maximum observé',
    },
    ...observationProtocolAttributes.map((attribute) => ({
      name: attribute.name,
      type: 'valeur',
      description: attribute.description,
    })),
  ];

  const objects: IndicatorExecutionContext['objects'] = {
    sites: {
      name: 'sites',
      type: 'MonitoringCollection',
      description: 'Ensemble des sites rattachés au protocole et à la sélection courante',
      attributes: sitesAttributes,
      itemType: 'Site',
      itemAttributes: siteItemAttributes,
    },
    visites: {
      name: 'visites',
      type: 'MonitoringCollection',
      description: 'Ensemble des visites de suivi effectuées sur les sites',
      attributes: visitsAttributes,
      itemType: 'Visit',
      itemAttributes: visitItemAttributes,
    },
    observations: {
      name: 'observations',
      type: 'MonitoringCollection',
      description: 'Ensemble des données d observation saisies sur les visites',
      attributes: observationsAttributes,
      itemType: 'Observation',
      itemAttributes: observationItemAttributes,
    },
    Scope: {
      name: 'Scope',
      type: 'Enum',
      description: 'Enumération des niveaux d agrégation GeoNature pour les calculs',
      attributes: [
        {
          name: 'OBSERVATION',
          type: 'Scope',
          description: 'Agrégation au niveau des observations',
        },
        {
          name: 'VISIT',
          type: 'Scope',
          description: 'Agrégation au niveau des visites',
        },
        {
          name: 'SITE',
          type: 'Scope',
          description: 'Agrégation au niveau des sites',
        },
        {
          name: 'GLOBAL',
          type: 'Scope',
          description: 'Agrégation globale sur toute la sélection',
        },
      ],
    },
    IndicatorError: {
      name: 'IndicatorError',
      type: 'Exception',
      description: 'Exception levée pour signaler une erreur métier dans l indicateur',
      attributes: [],
    },
    ref_statut_biologique: {
      name: 'ref_statut_biologique',
      type: 'ReferenceTable',
      description: 'Table de référence associée à l indicateur pour correspondance de données',
      attributes: [
        {
          name: 'code',
          type: 'string',
          description: 'Code identifiant de la table de référence',
        },
        {
          name: 'data',
          type: 'string',
          description: 'Contenu CSV brut de la table de référence',
        },
      ],
    },
  };

  const resolvedCampaignVariables =
    campaignVariables && campaignVariables.length > 0
      ? campaignVariables
      : ['médiane', 'moyenne', 'score_global', 'indice_abondance'];

  const campaignItemAttributes = [
    {
      name: 'start_date',
      type: 'datetime',
      description: 'Date de début de la campagne (ex: "2023-01-01")',
    },
    {
      name: 'end_date',
      type: 'datetime',
      description: 'Date de fin de la campagne (ex: "2023-12-31")',
    },
    {
      name: 'vars',
      type: 'CampaignVars',
      description: 'Variables calculées lors de la campagne (ex: vars.médiane)',
    },
  ];

  const campaignVarsAttributes = resolvedCampaignVariables.map((variableName) => ({
    name: variableName,
    type: 'PropertyCollection | float',
    description: `Variable calculée "${variableName}" pour la campagne`,
  }));

  const variablePropertyValueAttributes = [
    {
      name: 'values',
      type: 'List[PropertyValue]',
      description: 'Liste des valeurs calculées par entité (site ou visite)',
    },
    {
      name: 'value',
      type: 'float | int',
      description: 'Valeur scalaire unique calculée',
    },
  ];

  const variableNestedObjects = Object.fromEntries(
    resolvedCampaignVariables.map((variableName) => [
      variableName,
      {
        name: variableName,
        type: 'PropertyCollection',
        description: `Propriétés de la variable "${variableName}"`,
        attributes: variablePropertyValueAttributes,
      },
    ])
  );

  if (scope === 'overview' || scope === 'statistical-tests') {
    objects['campaigns'] = {
      name: 'campaigns',
      type: 'List[CampaignResult]',
      description: 'Liste des résultats de chaque campagne de suivi sélectionnée',
      attributes: [
        {
          name: 'start_date',
          type: 'datetime',
          description: 'Date de début de la campagne',
        },
        {
          name: 'end_date',
          type: 'datetime',
          description: 'Date de fin de la campagne',
        },
        {
          name: 'vars',
          type: 'CampaignVars',
          description: 'Variables calculées lors de la campagne',
        },
      ],
      itemType: 'CampaignResult',
      itemAttributes: campaignItemAttributes,
      nestedObjects: {
        vars: {
          name: 'vars',
          type: 'CampaignVars',
          description: 'Conteneur des variables de la campagne',
          attributes: campaignVarsAttributes,
          nestedObjects: variableNestedObjects,
        },
      },
    };
  }

  const functions: IndicatorExecutionContext['functions'] = [
    {
      name: 'gn_mean',
      signature:
        'gn_mean(prop_collection: PropertyCollection, scope: Scope = Scope.GLOBAL, weights: PropertyCollection = None) -> PropertyCollection',
      description:
        'Calcule la moyenne (globale ou groupée par site/visite) avec pondération optionnelle',
      returnType: 'PropertyCollection',
    },
    {
      name: 'gn_median',
      signature: 'gn_median(prop_collection: PropertyCollection) -> PropertyCollection',
      description: 'Calcule la médiane statistique d une collection de données',
      returnType: 'PropertyCollection',
    },
    {
      name: 'gn_extract',
      signature:
        'gn_extract(ref_table: ReferenceTable, origin_field: str, target_field: str, properties: PropertyCollection) -> PropertyCollection',
      description: 'Jointure de valeurs à partir d une table de référence CSV',
      returnType: 'PropertyCollection',
    },
    {
      name: 'len',
      signature: 'len(collection: Any) -> int',
      description: 'Renvoie le nombre d éléments d une collection ou d un tableau',
      returnType: 'int',
    },
    {
      name: 'round',
      signature: 'round(valeur: float, decimales: int = 2) -> float',
      description: 'Arrondit un nombre flottant au nombre de décimales spécifié',
      returnType: 'float',
    },
    {
      name: 'wilcoxon_test',
      signature: 'wilcoxon_test(serie1: List[float], serie2: List[float]) -> dict',
      description: 'Exécute le test statistique non-paramétrique de Wilcoxon-Mann-Whitney',
      returnType: 'dict',
    },
    {
      name: 'chi2_test',
      signature: 'chi2_test(tableau_contingence: List[List[int]]) -> dict',
      description: 'Exécute le test du Chi-carré d indépendance',
      returnType: 'dict',
    },
  ];

  return { objects, functions };
}
