# Rapport d'analyse et passation — Market Data Pipeline

## Périmètre de l'analyse

Analyse des fichiers propres au projet : `main.py`, `pyproject.toml`, `schema.sql`, `.vscode/settings.json`, `src/`, `tests/`, `.env` (présence et noms de variables uniquement) et les métadonnées de paquet présentes. Les environnements Python (`venv`, `.venv`, `.venv-1`), caches et bibliothèques installées ne sont pas du code métier et n'ont pas été examinés fichier par fichier.

**Sécurité de la passation :** un fichier `.env` contenant des valeurs pour `DB_HOST`, `DB_PORT`, `DB_NAME`, `DB_USER` et `DB_PASSWORD` est présent. Ses valeurs ne sont volontairement pas reproduites ici. Ne pas transmettre ce fichier ni ses valeurs à une IA, ne pas les copier dans un rapport ou dans le dépôt. Vérifier si le fichier a déjà été suivi ou partagé ; si des identifiants réels ont été exposés, les renouveler. Aucun `.gitignore` n'a été trouvé à la racine du projet.

## Résumé exécutif

Le dépôt a dépassé le premier prototype : il possède un modèle Pydantic, un pipeline avec statistiques par symbole, un dépôt PostgreSQL, un schéma SQL, une configuration par variables d'environnement et un exemple de lancement. Toutefois, l'exécution principale demande explicitement `persist=False`, il n'y a ni tests de pipeline/base de données ni procédure d'initialisation de la table, et les erreurs de persistance sont interceptées puis masquées. Le résultat est donc un prototype qui démontre le flux mémoire, pas encore une ingestion durable de bout en bout.

## Architecture et flux actuels

```text
main.py (ticks fictifs codés en dur)
  -> MarketPipeline.ingest()
       -> validate_and_filter_ticks() -> MarketTick (Pydantic)
       -> liste en mémoire
       -> MarketRepository.insert_ticks() si persist=True
            -> paramètres DB_* chargés depuis l'environnement / .env
            -> PostgreSQL, table market_ticks
  -> MarketPipeline.compute_statistics() (agrégats en mémoire par symbole)
```

- **Modèle et validation — `src/schema.py`** : `MarketTick` exige un symbole, un prix supérieur à zéro, un volume entier positif ou nul ; nettoie et met le symbole en majuscules ; crée un horodatage UTC par défaut. `validate_and_filter_ticks` garde les entrées valides et journalise les erreurs de validation ainsi que les erreurs inattendues.
- **Traitement — `src/pipeline.py`** : conserve les ticks validés en mémoire ; calcule le total et les nombres, prix moyens et volumes cumulés par symbole. Le dépôt est injecté au constructeur ou créé par défaut.
- **Persistance — `src/repository.py`** : lit les paramètres PostgreSQL depuis les variables d'environnement, utilise `psycopg` et insère les ticks avec `executemany`. Une liste vide ne déclenche pas de connexion.
- **Schéma SQL — `schema.sql`** : crée `market_ticks` avec identifiant, symbole, prix, volume, horodatage et date de création ; contraintes sur prix/volume ; index composé `(symbol, timestamp)`. C'est un script SQL manuel, pas un mécanisme de migration exécuté par l'application.
- **Lancement — `main.py`** : configure le logging et injecte des exemples fictifs ; affiche les statistiques par symbole.
- **Tests — `tests/test_schema.py`** : trois tests ciblent normalisation et création d'un tick, prix invalide et filtrage des ticks invalides. Aucun test du pipeline, du dépôt PostgreSQL, de l'insertion ou de l'intégration complète n'a été trouvé.
- **Dépendances — `pyproject.toml`** : paquet Python >= 3.10, Pydantic, `psycopg[binary]`, `python-dotenv`; pytest est dans l'extra `dev`.
- **Configuration éditeur — `.vscode/settings.json`** : demande à VS Code d'utiliser un fichier d'environnement dans le terminal Python.
- **Paquet — `src/__init__.py`** : expose la version `0.1.0`.

## Problèmes et risques à traiter

### Priorité immédiate — erreurs et cohérence des données

1. **Échec de base masqué (`src/pipeline.py`)** : le pipeline journalise une exception de persistance puis retourne les ticks comme si l'ingestion avait abouti. Les ticks sont aussi ajoutés à la mémoire avant la tentative DB. Un appelant ne peut donc pas distinguer « validé et persisté » de « validé mais non persisté » ; les états mémoire et PostgreSQL divergent.
2. **Échec applicatif au code de sortie 0 (`main.py`)** : l'exception générale est capturée et seulement journalisée ; l'exécution peut sembler réussie à l'automatisation malgré un échec.
3. **Erreurs de validation inattendues avalées (`src/schema.py`)** : le `except Exception` permet de continuer en cas de bug interne. Ne supprimer silencieusement que les erreurs de données attendues (par exemple `ValidationError`) et faire remonter les défauts inattendus.
4. **Validations du modèle et contraintes DB pas entièrement alignées** : la table limite le symbole à 20 caractères et le prix à 4 décimales, sans limites équivalentes dans Pydantic ; PostgreSQL peut donc refuser ou arrondir des données acceptées par le modèle. Définir le contrat de précision et de longueur, puis le faire respecter avant l'insertion.
5. **Fuseau horaire** : le timestamp par défaut est UTC, mais un timestamp fourni sans fuseau n'est pas explicitement refusé ou normalisé. Garantir des horodatages timezone-aware avant écriture dans `TIMESTAMPTZ`.
6. **Répétitions** : aucune clé d'idempotence ni contrainte d'unicité n'empêche de réinsérer des ticks lors d'un rejeu ou d'une reprise après incident. Définir une stratégie d'identification/déduplication avec les règles métier.

### Fiabilité et exploitation

- L'application ne crée pas la table et n'applique pas `schema.sql` : il faut donc préparer la base manuellement. Ajouter un mécanisme de migration/versionnement ou documenter et automatiser explicitement l'initialisation.
- `main.py` utilise uniquement des données synthétiques et désactive la persistance (`persist=False`) ; aucun adaptateur de fournisseur, ingestion API/stream, ordonnanceur, reprise, backfill ou limitation de débit n'est présent.
- Les paramètres DB ont des valeurs par défaut, dont un mot de passe vide. Une configuration absente peut échouer tardivement et de façon peu claire. Valider la configuration au démarrage et signaler précisément les paramètres requis sans journaliser de secrets.
- `load_dotenv()` est appelé lors de l'import du dépôt, donc l'import a un effet de bord lié à la configuration locale. Préférer charger la configuration au point d'entrée et l'injecter.
- Les logs utilisent des f-strings et n'apportent pas encore de compteurs/identifiants de lot structurés. Ne pas journaliser les données brutes complètes en cas d'erreur si elles peuvent contenir des données sensibles.
- Le dépôt ne déclare pas de types de retour/paramètres partout ; l'interface des statistiques est un dictionnaire libre au lieu d'un contrat typé.

### Tests, packaging et documentation

- Les tests ne couvrent pas les statistiques vides/par symbole, l'injection du dépôt, les erreurs DB, les transactions, le volume, les timestamps naïfs ou l'alignement avec le schéma SQL.
- Aucun test d'intégration ne permet de vérifier l'insertion PostgreSQL ; prévoir une base isolée pour tests et ne jamais viser la base réelle de développement.
- `pyproject.toml` déclare `readme = "README.md"`, mais aucun `README.md` n'a été trouvé : la construction/installation du paquet peut échouer à cause de ce fichier manquant.
- Les imports utilisent `src.schema`, `src.pipeline`, etc. alors que le projet s'appelle `market-data-pipeline`. Clarifier le layout et le nom du paquet importable pour éviter une distribution surprenante.
- Plusieurs dossiers d'environnement existent (`venv`, `.venv`, `.venv-1`) ainsi que des métadonnées `egg-info` à la racine et sous `src`. Les métadonnées générées visibles ne sont pas toutes alignées sur la configuration actuelle. Unifier l'environnement, régénérer les artefacts de packaging et les exclure du contrôle de version.
- Aucun `.gitignore` racine n'a été trouvé. Ajouter au minimum les exclusions adaptées pour `.env`, environnements virtuels, caches, `__pycache__`, fichiers `.pyc` et métadonnées de build.
- Aucun `README`, pipeline CI, lint/type-check, gestionnaire de migrations ou configuration de déploiement n'a été trouvé.

## Prochaine étape de développement recommandée

**Rendre le parcours PostgreSQL testable et honnête avant d'ajouter un fournisseur de marché.** Ordre proposé :

1. Ajouter un `.gitignore` sûr et vérifier que `.env` et les environnements ne sont pas suivis ; ne jamais inclure de valeurs secrètes dans les logs ou le rapport.
2. Ajouter un `README.md` avec installation, variables requises (noms seulement), création de base/table et commandes de test.
3. Clarifier le contrat du modèle (symbole <= 20 caractères, précision monétaire, timestamps avec fuseau) et l'aligner avec `schema.sql`.
4. Modifier le pipeline pour que l'échec de persistance soit explicitement propagé, ou retourné via un résultat distinct et documenté ; ne pas annoncer une ingestion réussie lorsque PostgreSQL n'a pas accepté les ticks.
5. Ajouter des tests unitaires du pipeline avec un dépôt factice, puis des tests d'intégration isolés du repository (insertion, transaction et erreur), et vérifier que le script SQL est appliqué.
6. Reproduire l'environnement avec une seule méthode et exécuter tests/build depuis cet environnement.

Ne pas ajouter de vrai connecteur de marché tant que ce flux n'a pas un comportement d'échec défini et vérifié.

## Arborescence intégrale recensée

Arbre du workspace au moment de cette analyse. Les environnements sont indiqués, mais leur contenu (bibliothèques tierces) est volontairement résumé pour garder le rapport exploitable ; les caches et métadonnées générées sont eux aussi repérés sans lister leurs fichiers internes.

```text
market-data-pipeline/
├── .env                           # Configuration locale ; NE PAS transmettre
├── .pytest_cache/                 # Cache généré
├── .venv/                         # Environnement Python (dépendances exclues)
├── .venv-1/                       # Environnement Python supplémentaire
├── .vscode/
│   └── settings.json
├── main.py                        # Point d'entrée de démonstration
├── market_data_pipeline.egg-info/ # Métadonnées de build générées
├── PASSATION_PROJET.md            # Ce rapport
├── pyproject.toml                 # Configuration et dépendances
├── schema.sql                     # DDL PostgreSQL
├── venv/                          # Environnement Python supplémentaire
├── src/
│   ├── __init__.py
│   ├── pipeline.py
│   ├── repository.py
│   ├── schema.py
│   ├── __pycache__/               # Bytecode Python généré
│   └── market_data_pipeline.egg-info/ # Métadonnées générées
└── tests/
  ├── __init__.py
  ├── test_schema.py
  └── __pycache__/               # Bytecode Python généré
```

Les dossiers `__pycache__/` et fichiers `.pyc` peuvent également être présents à l'intérieur des répertoires Python ; ils sont générés et ne font pas partie du code source. Aucun `.gitignore` ni `README.md` n'a été trouvé à la racine au moment de l'analyse.

## Consignes pour l'IA qui reprend le projet

Relire le dépôt dans son état courant avant toute modification. Ne pas transmettre ni afficher les valeurs du `.env`. Commencer par la première étape ci-dessus, vérifier les erreurs propagées et les tests dans un environnement unique, et donner les commandes réellement exécutées ainsi que leurs résultats. Ne pas prétendre qu'une insertion PostgreSQL ou qu'une suite de tests a réussi sans l'avoir vérifié.
