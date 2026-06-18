# Service 4 — Chargement CSV vers MySQL

Service Flask permettant de charger des données CSV dans une table MySQL `donnees`.  
Il est le **fournisseur de données** pour le Service 3 (Étudiant C).

---

## Structure du projet

```
service4_csv_mysql/
├── app.py                  # Application Flask principale
├── requirements.txt        # Dépendances Python
├── schema.sql              # Schéma MySQL partagé avec Service 3
├── .env.example            # Variables d'environnement à copier en .env
├── tests.sh                # Script de tests curl
└── data/
    └── donnees_exemple.csv # Fichier CSV de démonstration
```

---

## Installation

```bash
cd service4_csv_mysql
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
```

Copier et remplir le fichier d'environnement :
```bash
cp .env.example .env
# Éditer .env avec vos identifiants MySQL
```

Initialiser la base de données :
```bash
mysql -u root -p < schema.sql
```

Lancer le service :
```bash
python app.py
# → http://localhost:5004
```

---

## Routes disponibles

### POST /upload/csv
Charge un fichier CSV dans la table `donnees`.

**Paramètre multipart :** `file` (fichier .csv, max 5 Mo)

**Réponse 201 (succès) :**
```json
{
  "statut": "success",
  "lignes_inserees": 22,
  "lignes_invalides_ignorees": 0,
  "message": "22 ligne(s) chargée(s) dans la table donnees"
}
```

**Codes d'erreur :**
| Code | Cause |
|------|-------|
| 400  | Fichier absent, nom vide, extension invalide, colonnes manquantes, CSV illisible |
| 413  | Fichier > 5 Mo |
| 500  | Erreur de connexion ou requête MySQL |

---

### GET /upload/series
Liste les séries chargées avec leur nombre de points et leur plage de dates.

**Réponse 200 :**
```json
{
  "series": [
    {"serie": "serie_A", "n_points": 8, "debut": "2024-01-15", "fin": "2024-01-22"},
    {"serie": "serie_B", "n_points": 8, "debut": "2024-01-15", "fin": "2024-01-22"},
    {"serie": "serie_C", "n_points": 6, "debut": "2024-01-15", "fin": "2024-01-20"}
  ],
  "total": 3
}
```

---

## Format CSV attendu

| Colonne      | Type   | Obligatoire | Description                        | Exemple      |
|-------------|--------|-------------|-------------------------------------|--------------|
| nom_serie   | Texte  | Oui         | Identifiant de la série             | serie_A      |
| valeur      | Nombre | Oui         | Valeur numérique mesurée            | 12.50        |
| categorie   | Texte  | Non         | Catégorie thématique                | temperature  |
| date_mesure | Date   | Non         | Date au format YYYY-MM-DD           | 2024-01-15   |

---

## Tests curl

```bash
# Charger le CSV de démonstration
curl -X POST http://localhost:5004/upload/csv \
     -F 'file=@data/donnees_exemple.csv'

# Lister les séries
curl http://localhost:5004/upload/series
```

Ou lancer tous les tests d'un coup :
```bash
chmod +x tests.sh && ./tests.sh
```

---

## Réponses aux questions de vérification

### Q1. Quels contrôles de validation effectuez-vous avant d'insérer les données dans MySQL ?

1. **Présence du fichier** : la clé `file` doit exister dans la requête multipart.
2. **Nom de fichier non vide** : `file.filename != ''`.
3. **Extension `.csv`** : rejet de tout autre format.
4. **Taille max 5 Mo** : rejet avant lecture si le contenu dépasse la limite.
5. **Lisibilité CSV** : `pd.read_csv()` encapsulé dans un try/except.
6. **Colonnes obligatoires** : `nom_serie` et `valeur` doivent être présentes.
7. **Valeur numérique** : conversion via `pd.to_numeric(errors='coerce')` — les lignes non convertibles sont comptées puis supprimées.
8. **DataFrame non vide** : rejet si toutes les lignes sont invalides.

---

### Q2. Que se passe-t-il si le CSV contient des valeurs non numériques dans la colonne « valeur » ?

```python
df['valeur'] = pd.to_numeric(df['valeur'], errors='coerce')
lignes_invalides = df['valeur'].isna().sum()
df.dropna(subset=['valeur'], inplace=True)
```

- Les cellules non numériques sont converties en `NaN`.
- Leur nombre est comptabilisé dans `lignes_invalides`.
- Elles sont **supprimées** du DataFrame (pas d'insertion).
- Les lignes restantes valides sont insérées normalement.
- Le champ `lignes_invalides_ignorees` dans la réponse JSON indique combien ont été ignorées.

**Exemple** : CSV de 5 lignes dont 2 ont `valeur = "abc"` → réponse `lignes_inserees: 3, lignes_invalides_ignorees: 2`.

---

### Q3. Comment avez-vous coordonné le schéma MySQL avec l'Étudiant C (Service 3) ?

Le fichier **`schema.sql`** est partagé dans le dépôt Git et définit la table commune :

```sql
CREATE TABLE IF NOT EXISTS donnees (
    id          INT AUTO_INCREMENT PRIMARY KEY,
    nom_serie   VARCHAR(100)  NOT NULL,
    valeur      DOUBLE        NOT NULL,
    categorie   VARCHAR(100)  DEFAULT NULL,
    date_mesure DATE          DEFAULT NULL,
    created_at  TIMESTAMP     DEFAULT CURRENT_TIMESTAMP
);
```

Points de coordination :
- **Service 4** (ce service) écrit dans `donnees`.
- **Service 3** lit depuis `donnees` pour effectuer les calculs statistiques.
- Le nom de table et les colonnes sont identiques des deux côtés.
- Un index sur `nom_serie` accélère les `GROUP BY` du Service 3.
- Les deux services utilisent les mêmes variables `.env` (`DB_HOST`, `DB_USER`, `DB_PASSWORD`, `DB_NAME`).

---

### Q4. Testez l'envoi d'un CSV avec une colonne « valeur » manquante.

```bash
echo "nom_serie,categorie
serie_X,temperature" > /tmp/sans_valeur.csv

curl -X POST http://localhost:5004/upload/csv \
     -F 'file=@/tmp/sans_valeur.csv'
```

**Réponse obtenue (HTTP 400) :**
```json
{
  "erreur": "Colonnes obligatoires manquantes",
  "manquantes": ["valeur"]
}
```

---

### Q5. Après avoir chargé donnees_exemple.csv, quel est le résultat de la description de serie_C via le Service 3 ?

`serie_C` contient 6 points de mesure (débit, du 15 au 20 janvier 2024) :
`220.5, 235.8, 198.2, 245.1, 210.9, 228.4`

| Statistique | Valeur         |
|-------------|----------------|
| count       | 6              |
| mean        | 223.15         |
| std         | 17.15 (approx) |
| min         | 198.2          |
| 25%         | 211.575        |
| 50% (médiane) | 224.45       |
| 75%         | 233.85         |
| max         | 245.1          |

> Ces valeurs sont celles que le Service 3 retournera via son endpoint de description statistique pour `serie_C`.
