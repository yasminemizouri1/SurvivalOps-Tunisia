# Pitch Flash-Audit S1 (4 min chrono)

Répartition : **Yasmine** = minutes 1 et 3 ; **Ayoub** = minute 2 ; les deux = minute 4.

## Minute 1 — Problème métier (A)
« Lors d'une catastrophe, un opérateur de protection civile doit décider vite en croisant des guides de procédures, des stocks chiffrés, des relations entre abris et routes, et une carte. Aujourd'hui, tout est dispersé. Une recherche par mots-clés ne sait pas répondre à "150 survivants, 8 jours de nourriture, épidémie près de l'abri Alpha : que faire ?", car la réponse exige du calcul, du graphe et des procédures. Nous utilisons un scénario zombie fictif sur une carte de la Tunisie, mais les données et méthodes sont réelles : CDC, Ready.gov, FEMA. »

## Minute 2 — Architecture et ingestion (B)
- Un **routeur agentique** envoie la question à : **RAG hybride** (Qdrant dense + BM25, fusion RRF, Cross-Encoder), **SQL** (PostgreSQL, les chiffres ne viennent jamais du LLM), **Neo4j** (abris, routes, menaces).
- Ingestion : PDF/HTML → *parent-document chunking* → embeddings multilingues `bge-m3` → Qdrant avec métadonnées.
- Pourquoi Qdrant : filtrage par métadonnées et hybride natifs, un seul conteneur.
- API FastAPI async avec streaming SSE, front React avec carte Leaflet (Tunisie + zoom pilote Grand Tunis).
- Une plateforme intégrée : quatre axes (Hybrid RAG, GraphRAG, multimodal limité, routage agentique contrôlé) démontrés à profondeurs différentes dans un seul scénario. Événements et abris générés et étiquetés fictifs.

## Minute 3 — Métriques et backlog (A)
- Retrieval : Recall@5 ≥ 0,80, NDCG@10 ≥ 0,70.
- Génération (Ragas) : Faithfulness ≥ 0,85, Answer Relevance ≥ 0,80.
- Agent : routage ≥ 90 %. Calculs SQL : 100 %. Latence 1er token < 800 ms.
- Expérience : BM25 vs dense vs hybride vs hybride + reranker.
- Must Have : ingestion, hybride + reranker, SQL, graphe, routeur, API SSE, dashboard, CI/CD. Could Have : mode jeu « Jour suivant ».

## Minute 4 — Q&A (A + B)
Réponses prêtes :

| Question probable | Réponse courte |
|---|---|
| Pourquoi pas un simple LLM ? | Il invente des chiffres et des procédures. Nous imposons preuves, SQL et citations. |
| Pourquoi un graphe ? | Les routes, abris et menaces sont des relations : chemins et voisinage se requêtent naturellement. |
| Pourquoi Qdrant ? | Filtrage métadonnées + hybride natifs, léger. pgvector en repli. |
| Les données zombies sont fausses, c'est un gadget ? | La logique est réelle : gestion de crise, guides officiels, catastrophes réelles. Le zombie n'est qu'un scénario de simulation. |
| Risque principal ? | Hallucination : refus si preuve insuffisante, citations obligatoires, Ragas. |
| Et si vous manquez de temps ? | MVP gelé après la semaine 1. Le mode jeu, le multimodal et PostGIS sont Could Have ; le cœur RAG + SQL + graphe est protégé. |
| Quatre systèmes avancés en 7 semaines ? | Non : une plateforme intégrée, quatre axes à profondeurs différentes. Hybrid RAG complet, GraphRAG petit, multimodal en tranche, routeur contrôlé. |
| Routage réel ? | Routes simplifiées entre installations du Grand Tunis dans Neo4j ; PostGIS en extension. Pas de trafic réel. |
| Volumétrie cible ? | ~1 500 pages de guides, 50 000 déclarations FEMA, 10 000 événements simulés. |

**À répéter :** chronométrer deux fois, ne pas dépasser 4 min.
