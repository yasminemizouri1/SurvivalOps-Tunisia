-- SurvivalOps Tunisia : schema PostgreSQL de base
-- Les calculs de besoins (backlog M3) lisent ces tables.
-- Aucun chiffre ne vient du LLM : tout est calcule en SQL.
--
-- Calcul de reference du backlog :
--   150 survivants x 30 jours x 3,785 L/personne/jour (1 gallon) = 17 032,5 L
--   soit environ 17 033 L d'eau.

CREATE TABLE IF NOT EXISTS resources (
    id        SERIAL PRIMARY KEY,
    type      TEXT    NOT NULL,                       -- 'eau', 'nourriture', ...
    quantity  NUMERIC NOT NULL CHECK (quantity >= 0), -- quantite en stock
    unit      TEXT    NOT NULL                        -- 'L', 'kg', ...
);

CREATE TABLE IF NOT EXISTS shelters (
    id            SERIAL PRIMARY KEY,
    name          TEXT    NOT NULL,
    governorate   TEXT    NOT NULL,                   -- un des 24 gouvernorats
    capacity      INTEGER NOT NULL CHECK (capacity >= 0),
    risk_level    TEXT,                               -- 'faible', 'moyen', 'eleve'
    is_fictional  BOOLEAN NOT NULL DEFAULT TRUE       -- donnee inventee pour le scenario
);

CREATE TABLE IF NOT EXISTS events (
    id            SERIAL PRIMARY KEY,
    type          TEXT NOT NULL,                      -- 'epidemie', 'attaque', ...
    event_date    DATE,
    governorate   TEXT,
    is_fictional  BOOLEAN NOT NULL DEFAULT TRUE
);