# Flask Services Kanban
**TP2 de R210_GPO** — Système de microservices Flask pour le traitement de données, calculs statistiques et gestion d'une base de données MySQL.

---

## 📋 Vue d'ensemble

Ce projet implémente une **architecture de 5 microservices Flask** interconnectés, permettant :
- ✅ Calcul de matrices et résolutions algébriques
- 📊 Analyses statistiques sur des données
- 📤 Chargement de fichiers CSV vers MySQL
- 🔍 Requêtes statistiques depuis une base MySQL
- 🔗 Conversion et intégration C/Python

---

## 🏗️ Architecture

```
flask-services-kanban/
├── service1_matrices/          # Calculs matriciels
├── service2_statistiques/      # Analyses statistiques (en mémoire)
├── service3_stats_mysql/       # Requêtes statistiques depuis MySQL
├── service4_csv_mysql/         # Chargement CSV → MySQL
├── service5_c_python/          # Intégration C et Python
├── SQL/                        # Schémas et scripts SQL
├── data/                       # Données d'exemple
└── README.md
```

### Dépendances entre services

```
service4_csv_mysql (écrit dans MySQL donnees)
           ↓
service3_stats_mysql (lit depuis MySQL donnees)
           ↓
service1/2 + service5 (traitement complémentaire)
```

---

## 🚀 Installation rapide

### Prérequis
- Python 3.8+
- MySQL 5.7+ ou MariaDB
- pip

### Démarrage global

```bash
# 1. Cloner le dépôt
git clone https://github.com/Thenu196/flask-services-kanban.git
cd flask-services-kanban

# 2. Initialiser la base MySQL
mysql -u root -p < SQL/schema.sql

# 3. Lancer chaque service (dans des terminaux distincts)
cd service1_matrices && python app.py      # Port 5001
cd service2_statistiques && python app.py  # Port 5002
cd service3_stats_mysql && python app.py   # Port 5003
cd service4_csv_mysql && python app.py     # Port 5004
cd service5_c_python && python app.py      # Port 5005
```

---

## 📦 Services détaillés

### Service 1 : Matrices (Port 5001)
Calculs matriciels et résolutions algébriques.

**Endpoints principaux :**
- `POST /matrix/inverse` — Inverse d'une matrice
- `POST /matrix/solve` — Résolution de systèmes linéaires
- `POST /matrix/determinant` — Déterminant

```bash
curl -X POST http://localhost:5001/matrix/inverse \
     -H 'Content-Type: application/json' \
     -d '{"matrix": [[1, 2], [3, 4]]}'
```

---

### Service 2 : Statistiques (Port 5002)
Analyses statistiques sur données en mémoire.

**Endpoints principaux :**
- `POST /stats/describe` — Statistiques descriptives
- `POST /stats/correlation` — Matrice de corrélation
- `POST /stats/regression` — Régression linéaire

```bash
curl -X POST http://localhost:5002/stats/describe \
     -H 'Content-Type: application/json' \
     -d '{"data": [1, 2, 3, 4, 5]}'
```

---

### Service 3 : Statistiques MySQL (Port 5003)
Requêtes statistiques depuis la table MySQL `donnees`.

**Endpoints principaux :**
- `GET /stats/series/<serie_name>` — Description statistique d'une série
- `GET /stats/series` — Liste toutes les séries avec leurs stats

```bash
curl http://localhost:5003/stats/series
curl http://localhost:5003/stats/series/serie_A
```

---

### Service 4 : CSV → MySQL (Port 5004)
Chargement de fichiers CSV dans MySQL.

**Endpoints principaux :**
- `POST /upload/csv` — Charger un fichier CSV
- `GET /upload/series` — Lister les séries chargées

**Format CSV attendu :**
```csv
nom_serie,valeur,categorie,date_mesure
serie_A,12.50,temperature,2024-01-15
serie_A,13.75,temperature,2024-01-16
```

```bash
curl -X POST http://localhost:5004/upload/csv \
     -F 'file=@data/donnees_exemple.csv'
```

---

### Service 5 : Intégration C/Python (Port 5005)
Passerelle entre code C compilé et l'écosystème Python.

**Endpoints principaux :**
- `POST /compute/native` — Exécution de code C natif

```bash
curl -X POST http://localhost:5005/compute/native \
     -H 'Content-Type: application/json' \
     -d '{"function": "compute", "args": [...]}'
```

---

## 🗄️ Base de données

### Schéma MySQL

La table commune `donnees` partagée entre Service 3 et Service 4 :

```sql
CREATE TABLE donnees (
    id          INT AUTO_INCREMENT PRIMARY KEY,
    nom_serie   VARCHAR(100)  NOT NULL,
    valeur      DOUBLE        NOT NULL,
    categorie   VARCHAR(100)  DEFAULT NULL,
    date_mesure DATE          DEFAULT NULL,
    created_at  TIMESTAMP     DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_serie (nom_serie)
);
```

### Configuration d'accès

Tous les services utilisent les mêmes variables `.env` :

```env
DB_HOST=localhost
DB_USER=root
DB_PASSWORD=your_password
DB_NAME=flask_kanban
```

---

## 🧪 Tests

### Tests curl pour chaque service

```bash
# Service 4 : Charger CSV
curl -X POST http://localhost:5004/upload/csv \
     -F 'file=@data/donnees_exemple.csv'

# Service 3 : Consulter les séries
curl http://localhost:5003/upload/series

# Service 3 : Statistiques d'une série
curl http://localhost:5003/stats/series/serie_A

# Service 2 : Analyse statistique en mémoire
curl -X POST http://localhost:5002/stats/describe \
     -H 'Content-Type: application/json' \
     -d '{"data": [10, 20, 30, 40, 50]}'

# Service 1 : Calcul matriciel
curl -X POST http://localhost:5001/matrix/determinant \
     -H 'Content-Type: application/json' \
     -d '{"matrix": [[1, 2], [3, 4]]}'
```

### Lancement de suites de tests

Chaque service dispose d'un fichier `tests.sh` :

```bash
cd service4_csv_mysql && chmod +x tests.sh && ./tests.sh
```

---

## 📊 Flux d'utilisation typique

1. **Service 4** : Charger un fichier CSV via `/upload/csv`
2. **Service 3** : Consulter les données via `/stats/series`
3. **Service 2** : Calculer des statistiques sur un échantillon
4. **Service 1** : Résoudre des systèmes algébriques
5. **Service 5** : Optimiser via du code C natif si besoin

---

## 🔧 Configuration

### Variables d'environnement

Chaque service require un fichier `.env` à sa racine :

```bash
cp service1_matrices/.env.example service1_matrices/.env
# Éditer et adapter pour chaque service
```

### Ports utilisés

| Service | Port | Rôle |
|---------|------|------|
| Service 1 | 5001 | Matrices |
| Service 2 | 5002 | Statistiques (mémoire) |
| Service 3 | 5003 | Statistiques (MySQL) |
| Service 4 | 5004 | CSV → MySQL |
| Service 5 | 5005 | Intégration C/Python |

---

## 📝 Structure des données

### Exemple : Fichier CSV de démonstration

```csv
nom_serie,valeur,categorie,date_mesure
serie_A,10.5,temperature,2024-01-15
serie_A,12.3,temperature,2024-01-16
serie_B,45.2,pression,2024-01-15
serie_C,220.5,debit,2024-01-15
```

### Réponse Service 3 (describe)

```json
{
  "serie": "serie_A",
  "count": 8,
  "mean": 11.75,
  "std": 1.23,
  "min": 10.2,
  "25%": 11.1,
  "50%": 11.8,
  "75%": 12.4,
  "max": 13.5
}
```

---

## 🛠️ Développement

### Structure type d'un service

```
serviceN_xxx/
├── app.py              # Application Flask
├── requirements.txt    # Dépendances pip
├── .env.example        # Variables d'environnement
├── tests.sh            # Tests curl
└── data/
    └── exemple.csv
```

### Installation locale d'un service

```bash
cd serviceN_xxx
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
python app.py
```

---

## 🐛 Dépannage

### Service ne démarre pas
```bash
# Vérifier le port disponible
lsof -i :5001

# Lancer en debug
FLASK_ENV=development python app.py
```

### Erreur de connexion MySQL
```bash
# Vérifier service MySQL
mysql -u root -p -e "SELECT 1;"

# Vérifier variables .env
cat .env
```

### Fichier CSV rejeté (Service 4)
- Vérifier l'en-tête : `nom_serie`, `valeur` obligatoires
- Vérifier le format des dates : `YYYY-MM-DD`
- Vérifier que `valeur` contient uniquement des nombres

---

## 📚 Documentation additionnelle

Chaque service possède son propre README détaillé :
- [Service 1 - Matrices](./service1_matrices/README.md)
- [Service 2 - Statistiques](./service2_statistiques/README.md)
- [Service 3 - Stats MySQL](./service3_stats_mysql/README.md)
- [Service 4 - CSV MySQL](./service4_csv_mysql/README.md)
- [Service 5 - C/Python](./service5_c_python/README.md)

---

## 👥 Auteur

**Thenu196** — TP2 de R210_GPO

---

## 📄 Licence

À adapter selon les besoins du cours.

---

## ✅ Checklist de déploiement

- [ ] Base MySQL créée et accessible
- [ ] Variables d'environnement configurées
- [ ] 5 services en cours d'exécution
- [ ] Tests curl passants
- [ ] Fichier CSV exemple chargé
- [ ] Données visibles dans Service 3
