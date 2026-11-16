# Backlog MoSCoW — SurvivalOps Tunisia

Jalon final : **Séance 7 (soutenance, 40 % de la note)**. Chaque User Story porte un critère d'acceptation mesurable.

**Principes :** une seule plateforme intégrée qui démontre Hybrid RAG, GraphRAG, RAG multimodal (tranche limitée) et routage agentique contrôlé à travers un scénario unique. **MVP gelé à la fin de la semaine 1.** Intégration continue : une question doit traverser le routeur vers RAG + SQL dès la semaine 3. Ordre de coupe si retard : C1 (jeu), C6 (multimodal), C5 (PostGIS), puis C3.

## MUST HAVE (indispensables pour la S7)

| ID | User Story | Critères d'acceptation | Qui | Sem. |
|---|---|---|---|---|
| M1 | En tant qu'opérateur, je veux que les guides (Ready.gov, CDC, OMS) soient ingérés et découpés pour retrouver une procédure précise. | ≥ 15 docs ingérés ; chunking parent-document ; métadonnées `source/type/page` ; script rejouable (`make ingest`). | A | 2 |
| M2 | En tant qu'opérateur, je veux une recherche hybride (dense + BM25) avec reranker pour obtenir des passages pertinents. | Qdrant dense+sparse, fusion RRF, Cross-Encoder ; Recall@5 ≥ 0,80 sur le jeu de test. | A | 3 |
| M3 | En tant qu'opérateur, je veux que les besoins en nourriture/eau soient calculés depuis l'inventaire réel. | PostgreSQL ; « 150 survivants / 30 jours » → eau ≈ 17 033 L (tests unitaires) ; 100 % de justesse. | B | 3 |
| M4 | En tant qu'opérateur, je veux un graphe d'abris, de routes et de menaces pour trouver un chemin sûr. | Neo4j ≥ 10 abris/hôpitaux et ≥ 20 routes pondérées ; requête « chemin Abri A → Hôpital B » en évitant une zone infectée. | B | 3–4 |
| M5 | En tant qu'opérateur, je veux poser une question en langage naturel et que le système choisisse le bon outil. | Routeur RAG / SQL / Graphe ; précision ≥ 90 % sur 50 questions étiquetées ; décision journalisée. | A | 4–5 |
| M6 | En tant qu'opérateur, je veux une réponse avec citations des sources en streaming. | API FastAPI async + Pydantic v2 ; SSE ; latence 1er token < 800 ms ; chaque réponse cite ses chunks. | A | 3–5 |
| M7 | En tant qu'opérateur, je veux un tableau de bord avec la carte de la Tunisie (vue d'ensemble) et un zoom pilote sur le Grand Tunis, l'état des abris et la réponse. | React ; carte Leaflet des 24 gouvernorats + couche Grand Tunis ; abris colorés par niveau de risque ; page ressources ; chat avec citations ; tous les événements étiquetés « fictif ». | B | 4–6 |
| M11 | En tant qu'opérateur, je veux un outil géospatial à interface stable (`find_safe_route(origine, destination, zones_a_eviter)`) pour obtenir un itinéraire sûr. | Version MVP sur arêtes pondérées Neo4j entre abris/hôpitaux du Grand Tunis ; renvoie chemin + distance ; appelé par le routeur ; testé. L'implémentation peut être remplacée par PostGIS sans changer l'interface. | B | 4 |
| M8 | En tant qu'équipe, nous voulons un pipeline CI/CD. | GitHub Actions : linter (ruff) + tests (pytest) à chaque push ; `main` protégée ; Conventional Commits. | B | 2 |
| M9 | En tant qu'équipe, nous voulons un environnement reproductible. | `docker compose up` lance Qdrant + PostgreSQL + Neo4j ; README à jour. | B | 1–2 |
| M10 | En tant qu'équipe, nous voulons évaluer la qualité du RAG. | Comparaison BM25 / dense / hybride / hybride+reranker sur ≥ 50 questions ; tableau de résultats dans `docs/evaluation.md`. | A | 6 |

## SHOULD HAVE (forte valeur)

| ID | User Story | Critères d'acceptation |
|---|---|---|
| S1 | Évaluation continue Ragas journalisée (Langfuse) | Faithfulness ≥ 0,85 ; scores sauvegardés à chaque exécution. |
| S2 | Cache sémantique Redis pour les questions fréquentes | Taux de hit mesuré ; latence réduite d'au moins 50 % sur requêtes en cache. |
| S3 | Garde-fous : filtrage PII et refus si preuve insuffisante | Réponse « information non disponible » si score < seuil ; test sur 10 cas pièges. |
| S4 | Générateur d'événements d'épidémie simulés | ≥ 500 événements JSON/PostgreSQL, reproductibles (seed fixe). |

## COULD HAVE (différenciateurs M2)

| ID | User Story | Critères d'acceptation |
|---|---|---|
| C1 | Mode « jeu » : bouton « Jour suivant » (consommation, propagation) | Les stocks diminuent, l'épidémie se propage entre gouvernorats voisins, journal d'événements. |
| C2 | Plan de survie multi-étapes (RAG + SQL + Graphe dans une même réponse) | Scénario démo : 150 survivants, 8 jours de nourriture, épidémie près d'Alpha → plan complet. |
| C3 | Prédiction de rupture de stock | Date de rupture estimée par ressource, alerte sur le dashboard. |
| C4 | Manifestes Kubernetes | Deployments/Services pour l'API et les bases. |
| C5 | Requêtes PostGIS (distance, « installation la plus proche ») derrière l'interface géospatiale de M11 | Au moins 2 requêtes PostGIS testées ; l'outil `find_safe_route` fonctionne avec ou sans PostGIS. À faire en fin de projet (sem. 6) si le temps le permet. |
| C6 | Tranche multimodale : tableaux et quelques images/cartes | Extraction de tableaux de 2–3 PDF ; légendes d'images générées par un modèle de vision à l'ingestion ; indexées dans Qdrant ; au moins 5 questions de test multimodales. |

## WON'T HAVE (exclus du MVP)

- Fine-tuning d'un LLM.
- Import complet du réseau routier OpenStreetMap et routage routier réel (pgRouting) : routes simplifiées saisies à la main dans Neo4j ; PostGIS seulement en C5.
- Redis, plusieurs LLM, frameworks d'orchestration supplémentaires.
- Agent autonome de planification : le routeur est contrôlé (choix d'outils + combinaison des résultats).
- Gestion complète des profils de survivants (compétences, équipes).
- Authentification multi-utilisateurs / facturation.
- Moteur de jeu 3D (Unity, Phaser).
