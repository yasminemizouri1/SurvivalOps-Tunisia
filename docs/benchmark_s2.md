# Benchmark Recall@5

10 requêtes (benchmark_queries.md), filtre de catégorie : non.

| Exécution (collection=modèle) | Recall@5 (doc + page) | Recall@5 (doc seul) |
|---|---|---|
| `guides=intfloat/multilingual-e5-small` | 0.70 (7/10) | 0.80 (8/10) |
| `guides_bge=BAAI/bge-m3` | 0.70 (7/10) | 0.90 (9/10) |

## Détail par requête (rang du premier bon résultat, « - » = absent du Top-k)

| # | Question | `guides` | `guides_bge` |
|---|---|---|---|
| 1 | Comment rendre l'eau potable en urgence ? | - | 1 |
| 2 | Combien de gouttes d'eau de Javel pour 1 gallon ? | - | - |
| 3 | Combien de temps la nourriture reste-t-elle sûre dans un frigo sans électricité ? | 4 | 3 |
| 4 | Quelle quantité minimale d'eau par personne et par jour ? | 4 | doc 1 |
| 5 | Que mettre dans un kit d'urgence ? | 1 | 1 |
| 6 | Comment nettoyer sa maison après une inondation ? | 1 | 1 |
| 7 | Quelles sont les étapes du contrôle d'une épidémie en situation d'urgence ? | doc 2 | 2 |
| 8 | Qu'est-ce qu'une équipe médicale d'urgence (EMT) de type 1 ? | 3 | 1 |
| 9 | Comment préparer un plan d'urgence pour une personne âgée ? | 5 | doc 1 |
| 10 | Comment éviter l'intoxication au monoxyde de carbone pendant une panne de courant ? | 4 | 2 |
