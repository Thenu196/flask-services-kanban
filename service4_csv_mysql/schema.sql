-- Schéma MySQL partagé entre Service 3 (Étudiant C) et Service 4 (Étudiant D)
-- À exécuter une seule fois pour initialiser la base de données

CREATE DATABASE IF NOT EXISTS projet_db
    CHARACTER SET utf8mb4
    COLLATE utf8mb4_unicode_ci;

USE projet_db;

CREATE TABLE IF NOT EXISTS donnees (
    id            INT AUTO_INCREMENT PRIMARY KEY,
    nom_serie     VARCHAR(100)   NOT NULL,
    valeur        DOUBLE         NOT NULL,
    categorie     VARCHAR(100)   DEFAULT NULL,
    date_mesure   DATE           DEFAULT NULL,
    created_at    TIMESTAMP      DEFAULT CURRENT_TIMESTAMP
);

-- Index pour accélérer les requêtes du Service 3 (GROUP BY nom_serie)
CREATE INDEX IF NOT EXISTS idx_nom_serie ON donnees (nom_serie);
