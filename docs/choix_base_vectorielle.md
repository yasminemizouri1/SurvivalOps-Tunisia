# Choix de la base vectorielle : Qdrant

| Critère | Qdrant | Milvus | pgvector |
|---|---|---|---|
| Filtrage par métadonnées | Excellent (filtre intégré à la recherche HNSW) | Bon | Bon (SQL), plus lent à grande échelle |
| Recherche hybride dense + sparse | Native (vecteurs sparse + fusion) | Supportée | Via extension / à assembler |
| Latence | Faible (Rust) | Faible | Moyenne |
| Simplicité d'orchestration locale | 1 conteneur | Plusieurs services (etcd, MinIO) | Extension de PostgreSQL |
| Adapté à notre volume (~10⁵ chunks) | Oui | Surdimensionné | Oui |

**Décision : Qdrant.** Le filtrage sur `type_catastrophe`, `source` et `langue` est central pour nous, la recherche hybride est native, et un seul conteneur suffit en local. PostgreSQL reste dédié aux calculs d'inventaire, ce qui sépare clairement les responsabilités.

**Alternative écartée :** pgvector aurait réduit le nombre de services, mais la recherche hybride et le filtrage haute performance y sont moins directs. Milvus est trop lourd pour la taille de notre corpus.

**Plan de repli :** si Qdrant pose problème, migration vers pgvector (même base que l'inventaire).
