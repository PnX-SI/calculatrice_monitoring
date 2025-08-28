Module calculatrice monitoring pour GeoNature

# Installation du module

En considérant que le code source a été installé dans `~/calculatrice_monitoring` avec git clone ou une archive.

```bash
geonature install-gn-module ~/calculatrice_monitoring
```

# Préparation environnement de développement avec PyCharm

- on considère que ce projet est placé dans le même répertoire parent que le projet GeoNature (sinon ajuster le path de `frontend/tsconfig.json`)
- placer un lien symbolique vers le répertoire `node_modules` du frontend GeoNature à la racine du projet (`ln -s ../GeoNature/frontend/node_modules`)
- utiliser le virtualenv de GeoNature
- installer les dépendances frontend de développement (pour lancer les tests, le formatage auto)

Ce projet utilise `black`, `flake8`, `prettier` et `eslint` pour assurer la cohérence du style et les bonnes pratiques Python et TypeScript. Vérifier que PyCharm utilise les configurations fournies avec le projet pour auto-formater et linter le code.

# Lancer les tests backend

Les tests backend doivent être lancés sur une BD ne contenant pas d'objets du module calculatrice.

Dans le répertoire `calculatrice_monitoring` exécuter `pytest`.

# Lancer les tests frontend

Les tests frontend nécessitent que le module calculatrice ait été installé sur l'instance GeoNature locale et que le frontend et le backend soient démarrées.

Dans le répertoire `calculatrice_monitoring/frontend` exécuter `npx cypress run`.

# Vérifications automatiques

Pour exécuter localement les vérifications appliquées par la CI il faut activer `pre-commit` comme suit :

```bash
pre-commit install
```

Les vérifications suivantes sont exécutées :

- formatage black sur les fichiers python (modifications appliquées dans le staging de Git)
- formatage et organisation des imports python avec isort (modifications appliquées dans le staging de Git)
- formatage code frontend + organisation imports avec prettier (check-only, modifications à appliquer avec `npm run format`)

Note : pour le moment `prettier` vérifie l'intégralité des fichiers frontend à chaque commit, il n'est donc pas possible de commiter un fichier bien formaté si d'autres ne le sont pas. 
