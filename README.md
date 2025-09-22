Module calculatrice monitoring pour GeoNature

# Installation du module

En considérant que le code source a été installé dans `~/calculatrice_monitoring` avec git clone ou une archive.

```bash
geonature install-gn-module ~/calculatrice_monitoring
```

# Dépendances et versions

Le module calculatrice cible GeoNature v2.16.2 et gn_module_monitoring v1.1.0.

Le module `gn_module_monitoring` utilise plusieurs termes pour désigner les protocoles de suivi selon le contexte :
« protocoles », « modules » ou « sous-modules », « MonitoringModules ». Dans le cadre de ce module calculatrice le terme
_protocole_ sera privilégié autant que possible, que ce soit dans les interfaces utilisateurs ou dans le code.

# Préparation environnement de développement avec PyCharm

- on considère que ce projet est placé dans le même répertoire parent que le projet GeoNature (sinon ajuster le path de `frontend/tsconfig.json`)
- placer un lien symbolique vers le répertoire `node_modules` du frontend GeoNature à la racine du projet (`ln -s ../GeoNature/frontend/node_modules`)
- utiliser le virtualenv de GeoNature
- installer les dépendances frontend de développement (pour lancer les tests, le formatage auto)

Ce projet utilise `ruff`, `prettier` et `eslint` pour assurer la cohérence du style et les bonnes pratiques Python et TypeScript. Vérifier que votre éditeur utilise les configurations fournies avec le projet pour auto-formater et linter le code.

# Convention pour les commits

Ce projet suit la convention [Conventional Commits](https://www.conventionalcommits.org/en/v1.0.0/).

Les messages de commits doivent être de la forme :

```
<type>[optional scope]: <description>

[optional body]

[optional footer(s)]
```

Par exemple :

- `feat(indicateur): add creation datetime`
- `docs: update README`

# Lancer les tests backend

Les tests backend doivent être lancés sur une BD ne contenant pas d'objets du module calculatrice. Voici la procédure
pour obtenir une BD de test :

1. à partir de la BD initialisée lors de l'installation standard de GeoNature
2. installer gn_module_monitoring 1.1.0 avec `geonature install-gn-module ./gn_module_monitoring --build false`
3. installer le module calculatrice `geonature install-gn-module ./calculatrice_monitoring --build false`

Puis dans le répertoire `calculatrice_monitoring` exécuter `pytest --cov`.

Pour l'étape 1. il est aussi possible de partir de l'image docker [geonature-db](https://github.com/PnX-SI/geonature_db) 
générée pour la version adéquate de GeoNature.

# Lancer les tests frontend

Les tests frontend nécessitent que le module calculatrice ait été installé sur l'instance GeoNature locale et
que le frontend et le backend soient démarrées.

Dans le répertoire `calculatrice_monitoring/frontend` exécuter `npx cypress run`.

# Vérifications automatiques

Pour exécuter localement les vérifications appliquées par la CI il faut activer `pre-commit` comme suit :

```bash
pre-commit install --install-hooks
```

Les vérifications suivantes sont exécutées :

- linter ruff sur les fichiers python (modifications appliquées directement si possible, sinon erreur dans les logs)
- formatage ruff sur les fichiers python (modifications appliquées directement)
- vérification que le message de commit suit la convention (commit échoue si ce n'est pas le cas)
- formatage code frontend + organisation imports avec prettier (check-only, modifications à appliquer avec `npm run format`)

Note : pour le moment `prettier` vérifie l'intégralité des fichiers frontend à chaque commit, il n'est donc pas possible de commiter un fichier bien formaté si d'autres ne le sont pas. 
