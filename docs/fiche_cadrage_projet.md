# Fiche de Cadrage — Projet Fédérateur IA & Big Data (M2)

**Projet :** SurvivalOps Tunisia — assistant décisionnel de gestion de crise (scénario fictif d'apocalypse zombie)
**Équipe :** <Yasmine MIZOURI> / <Ayoub LOUATI>
**Thématique :** RAG hybride + GraphRAG (Neo4j) + Text-to-SQL + routage agentique
**Date :** Séance 1

---

## 1. Description du problème métier

**Persona :** Karim (nom fictif), opérateur de protection civile / coordinateur de crise. Il gère plusieurs centres d'hébergement lors d'une catastrophe (inondation, incendie, séisme, contamination de l'eau) et doit décider vite avec des informations dispersées.

**Point de douleur :** en situation de crise, l'opérateur doit croiser quatre sources en même temps :
1. des **guides de procédures** (documents PDF/HTML longs) ;
2. des **stocks chiffrés** (nourriture, eau, médicaments) ;
3. des **relations** (quel abri est relié à quel hôpital, quelle route est coupée, quelle zone est menacée) ;
4. la **carte** de la situation.

Aujourd'hui, ces informations sont dans des documents, des tableurs et des cartes séparés. La décision est lente et sujette à erreur.

**Pourquoi une recherche par mots-clés (Elasticsearch seul) échoue :**
- Les questions sont multi-étapes : « Nous avons 150 survivants et 8 jours de nourriture, une épidémie est signalée près de l'abri Alpha : que faire ? » Aucun mot-clé ne répond à cela.
- La réponse exige du **calcul** (SQL), des **relations** (graphe) et des **procédures** (documents), pas seulement un passage de texte.
- Les synonymes et reformulations (« eau potable » / « contamination de l'approvisionnement ») cassent la recherche lexicale pure.

**Plus-value de l'IA générative :** un LLM qui ne devine jamais les chiffres. Il **route** la question vers le bon outil, **récupère des preuves** (RAG), **calcule** (SQL), **explore le graphe** (Neo4j), puis **rédige un plan cité**.

**Périmètre :** une plateforme intégrée d'aide à la décision qui démontre quatre axes à profondeurs différentes : Hybrid RAG (complet : dense + BM25 + reranker), GraphRAG (petit graphe Neo4j de 5–7 types d'entités), RAG multimodal (tranche limitée : tableaux de PDF et quelques images/cartes), routage agentique contrôlé (un routeur vers 4–5 outils). Zone pilote : vue Tunisie + zoom **Grand Tunis**. Tous les événements d'épidémie et états d'abris sont générés et explicitement étiquetés **fictifs** ; la carte fournit le contexte géographique, pas de menace réelle.

**Anti-gadget :** le scénario zombie est une simulation. Les connaissances (guides CDC/Ready.gov/OMS, catastrophes réelles) et la logique de gestion de crise sont réelles.

---

## 2. Source et volumétrie des données

| # | Source | Nature | Format | Volume test | Volume cible |
|---|---|---|---|---|---|
| 1 | Ready.gov, CDC (préparation aux urgences), OMS/Sphere | Guides de survie, eau, nourriture, santé | PDF / HTML | 15–20 docs (~300 pages) | 60–100 docs (~1 500 pages) |
| 2 | FEMA OpenFEMA — Disaster Declarations | Catastrophes historiques (dates, types, lieux) | JSON / CSV (API) | 5 000 lignes | 50 000+ lignes |
| 3 | Our World in Data | Statistiques population / ressources | CSV | 5–10 jeux | 20 jeux |
| 4 | Données Tunisie (HDX / OCHA / INS) — *à vérifier* | Limites des 24 gouvernorats, population | GeoJSON / CSV | 1 fichier GeoJSON | + hôpitaux et installations du Grand Tunis (OSM, sélection manuelle) |
| 5 | Événements d'épidémie simulés (générés par nous) | Infections, gravité, propagation, évacuations | JSON / PostgreSQL | 500 événements | 10 000 événements |
| 6 | Inventaire et abris simulés (générés) | Stocks, capacités, survivants | PostgreSQL / Neo4j | 12 abris, 150–500 survivants | 30 abris, 2 000 survivants |

**Nature des documents :** texte brut, PDF multi-colonnes, tableaux (rations, quantités d'eau), listes de contrôle.
**Remarque :** il n'existe aucun jeu de données réel sur les zombies. Nous combinons des données réelles (savoir-faire, catastrophes, géographie) et des données simulées (événements, stocks).

---

## 3. Stratégie d'ingestion et de vectorisation

- **Extraction :** PDF/HTML → texte propre (PyMuPDF / unstructured), conservation des titres et des tableaux.
- **Découpage :** *parent-document chunking* : petits fragments (~300 tokens) pour la précision de recherche, renvoi du passage parent (~1 200 tokens) au LLM pour le contexte. Découpage par titres/sections avant la taille fixe.
- **Métadonnées (filtrage à chaud) :** `source`, `type_catastrophe` (eau, médical, évacuation…), `langue`, `page`, `url`.
- **Embeddings denses :** `BAAI/bge-m3` ou `multilingual-e5-base` (multilingue FR/EN). Vecteurs **sparse** BM25 pour la recherche lexicale.
- **Base vectorielle :** **Qdrant** (voir `docs/choix_base_vectorielle.md`).
- **Retrieval :** hybride dense + sparse, fusion RRF, top-20 puis **Cross-Encoder** (`bge-reranker-v2-m3`) → top-5.
- **Multimodal (tranche limitée) :** extraction de tableaux de quelques PDF, légendes d'images/cartes générées par un modèle de vision, indexées dans Qdrant.
- **Autres bases :** PostgreSQL + PostGIS (inventaire, calculs, requêtes de distance), Neo4j (abris, routes pondérées, menaces, survivants). Outil géospatial à interface stable : MVP sur Neo4j, PostGIS ajouté en fin de projet si le temps le permet.
- **Évaluation et traçage :** Ragas + traçage Langfuse de base. Infrastructure : Docker Compose + GitHub Actions. Un seul LLM.
- **Orchestration :** routeur agentique (RAG / SQL / Graphe) via LlamaIndex ou LangChain. API FastAPI async, streaming SSE.

```
Question → Routeur agentique ┬→ RAG hybride (Qdrant + reranker) ┐
                             ├→ SQL (PostgreSQL)                ├→ LLM → plan cité + dashboard
                             └→ Graphe (Neo4j, routes/menaces)  ┘
```

---

## 4. Métriques de qualité

| Niveau | Métrique | Cible |
|---|---|---|
| Retrieval | Recall@5 | ≥ 0,80 |
| Retrieval | NDCG@10 | ≥ 0,70 |
| Retrieval | MRR | ≥ 0,65 |
| Génération (Ragas) | Faithfulness | ≥ 0,85 |
| Génération (Ragas) | Answer Relevance | ≥ 0,80 |
| Génération (Ragas) | Context Recall | ≥ 0,80 |
| Agent | Précision du routage (jeu de 50 questions étiquetées) | ≥ 90 % |
| Calcul | Exactitude des chiffres SQL (tests unitaires) | 100 % |
| Performance | Latence premier token (SSE) | < 800 ms |

**Expérience comparative :** BM25 seul, dense seul, hybride, hybride + reranker. Même jeu de 50–100 questions de test, résultats consignés dans un tableau.

---

## 5. Risques et garde-fous

| Risque | Garde-fou |
|---|---|
| Hallucination de chiffres | Tout chiffre vient de SQL, jamais du LLM. Le LLM doit citer sa source ; sinon « information non disponible ». |
| Hallucination de procédures | Réponse uniquement à partir des passages récupérés, citations obligatoires, seuil de score minimal. |
| Mauvais routage | Jeu de tests de routage, repli sur RAG, journalisation de la décision. |
| Fuite de données / PII | Données entièrement fictives pour les survivants, filtrage PII (Presidio) sur entrées/sorties. |
| Clés API committées | `.env` dans `.gitignore`, `.env.example` fourni, scan des secrets en CI. |
| Dérive de périmètre (carte, jeu) | Backlog MoSCoW strict ; la simulation de jeu est un « Could Have ». |
| Avertissement | Le système est une simulation pédagogique, il ne remplace pas les services d'urgence réels. |
