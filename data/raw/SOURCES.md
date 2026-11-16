# Sources des données brutes

Téléchargé le 2026-11-16. Les licences sont à confirmer avant publication du dépôt.

## Guides (RAG) — `guides/`

| Fichier | Pages | URL |
|---|---|---|
| `ready_gov_emergency_supply_list.pdf` | 2 | https://www.ready.gov/sites/default/files/2021-02/ready_checklist.pdf |
| `ready_gov_are_you_ready_guide.pdf` | 36 | https://www.ready.gov/sites/default/files/2021-11/are-you-ready-guide.pdf |
| `ready_gov_hazard_info_sheets.pdf` | 35 | https://www.ready.gov/sites/default/files/2025-02/fema_full-suite-hazard-info-sheets.pdf |
| `ready_gov_power_outage.pdf` | 2 | https://www.ready.gov/sites/default/files/2024-03/ready.gov_power-outage_hazard-info-sheet.pdf |
| `ready_gov_older_adults.pdf` | 20 | https://www.ready.gov/sites/default/files/2023-09/ready-gov_disaster-preparedness-guide-for-older-adults.pdf |
| `cdc_hurricane_flooding_messaging.pdf` | 60 | https://stacks.cdc.gov/view/cdc/56624/cdc_56624_DS1.pdf |
| `cdc_stacks_48338.pdf` | 38 | https://stacks.cdc.gov/view/cdc/48338/cdc_48338_DS1.pdf (titre à vérifier) |
| `who_communicable_disease_emergencies.pdf` | 301 | https://iris.who.int/server/api/core/bitstreams/a724030b-5825-4b5e-8577-b94ffa807f2d/content |
| `who_emt_blue_book_2021.pdf` | 82 | https://extranet.who.int/emt/sites/default/files/BlueBook2021.pdf |
| `who_wash_risk_management_2017.pdf` | 2 | https://cdn.who.int/media/docs/default-source/disaster-mngmt/risk-management-wash-december2017.pdf |
| `sphere_handbook_2018.pdf` | 458 | https://globalprotectioncluster.org/sites/default/files/2022-11/sphere-handbook-2018-en.pdf (copie ; version officielle : spherestandards.org) |

## Données — `fema/` et `geo/`

| Fichier | Contenu | URL |
|---|---|---|
| `fema/disaster_declarations.csv` | 10 000 déclarations de catastrophe FEMA les plus récentes (OpenFEMA v2) | https://www.fema.gov/api/open/v2/DisasterDeclarationsSummaries.csv?$top=10000&$orderby=declarationDate desc |
| `geo/tunisia_adm1.geojson` | 24 gouvernorats de Tunisie (geoBoundaries gbOpen, ODbL, source OpenStreetMap) | https://github.com/wmgeolab/geoBoundaries/raw/9469f09/releaseData/gbOpen/TUN/ADM1/geoBoundaries-TUN-ADM1.geojson |

## À récupérer manuellement (accès refusé aux téléchargements automatiques, erreur 403)

- CDC « Emergency Water Supply Planning Guide » : https://www.cdc.gov/water-emergency/media/pdfs/2024/07/emergency-water-supply-planning-guide-2019-508.pdf
- CDC « Make Water Safe During an Emergency » : https://www.cdc.gov/water-emergency/media/pdfs/make-water-safe-during-emergency-p.pdf
- FEMA « Basic Preparedness » : https://www.fema.gov/pdf/areyouready/basic_preparedness.pdf

Ouvrir ces liens dans le navigateur et enregistrer les PDF dans `guides/`.

## Hors projet

Les fichiers `*_10K_*.htm` / `*_10Q_*.htm` présents à la racine de `data/raw/` sont des rapports financiers SEC, sans lien avec ce projet.
