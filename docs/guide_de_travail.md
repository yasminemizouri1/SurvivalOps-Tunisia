# Guide de travail — Séance 1 (à suivre dans l'ordre)

## Avant la séance (maintenant, ~1 h)
1. **Remplacer les noms** : `<Prénom Nom 1/2>` dans `docs/fiche_cadrage_projet.md`, « Membre A/B » dans `README.md` et `docs/pitch_s1.md`.
2. **Créer le dépôt GitHub** (privé, invitez le professeur si demandé), puis :

```bash
cd D:/Study/projet_federateur
git init -b main
git add .
git commit -m "docs: initial project framing (S1)"
git remote add origin https://github.com/<user>/<repo>.git
git push -u origin main
```

3. **Vérifier** que `.env` n'est pas suivi : `git status` ne doit jamais le montrer.
4. Créer les dossiers vides : `data/raw`, `src`, `frontend`, `tests` (ajoutez un fichier `.gitkeep` dans chacun).

## Pendant le Sprint H2 (60 min) : répartition

| Minutes | Yasmine (A) | Ayoub (B) |
|---|---|---|
| 00–15 | Valider le sujet avec le prof, relire la fiche | Idem, préparer le dépôt |
| 15–35 | Relire/ajuster sections 3–4 (ingestion, métriques) | Relire/ajuster sections 1, 2, 5 |
| 35–50 | Relire le backlog (M1, M2, M5, M6, M10) | Relire le backlog (M3, M4, M7–M9) |
| 50–60 | Push final, répéter minutes 1 et 3 | Vérifier `.gitignore`, répéter minute 2 |

## Avant la Séance 2 : livrables (sur `main`)

| Livrable | Action concrète | Qui |
|---|---|---|
| Corpus dans `data/raw/` | Télécharger 10–15 PDF : Ready.gov (eau, nourriture, kit d'urgence, premiers secours), CDC Emergency Preparedness, guides OMS ; export FEMA Disaster Declarations (CSV via OpenFEMA) ; GeoJSON des gouvernorats de Tunisie (HDX / geoBoundaries) | A : PDF, B : FEMA + GeoJSON |
| README finalisé | Déjà fait : ajouter un schéma (export image du diagramme) | B |
| Choix de la base vectorielle | Déjà rédigé : `docs/choix_base_vectorielle.md` | A |
| `docker-compose.yml` | Copier `.env.example` en `.env`, lancer `docker compose up -d`, vérifier les 3 interfaces | B |

Ne pas committer de fichiers lourds (> 50 Mo) ; mentionner leurs sources dans `data/raw/SOURCES.md`.

## Les 6 semaines suivantes (résumé)

| Sem. | Objectif | A | B |
|---|---|---|---|
| 2 | Ingestion | chunking + Qdrant | schéma PostgreSQL + données simulées + CI |
| 3 | Retrieval | hybride + reranker + API SSE | Neo4j + requêtes de routes |
| 4 | Outils | baseline Ragas + routeur | outils SQL + carte avec vraies données |
| 5 | Intégration | plans multi-étapes | dashboard + « Jour suivant » |
| 6 | Évaluation | comparaison BM25/dense/hybride/rerank, garde-fous | tests, CI/CD, Docker |
| 7 | Soutenance | répétition démo | répétition démo |

**Règle d'or :** si le retard s'installe, couper d'abord le mode jeu (C1), puis la prédiction (C3). Ne jamais sacrifier : hybride + reranker, évaluation Ragas, CI/CD.
