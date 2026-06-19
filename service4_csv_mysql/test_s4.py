"""
Tests unitaires — Service 4 : Chargement CSV vers MySQL
Port : 5004

Les tests couvrent :
  - /upload/csv    (cas nominal + validations fichier + validations colonnes)
  - /upload/series (liste des séries après chargement)
"""

import unittest
import requests
import json
import io

BASE_URL = "http://localhost:5004"


# ─── Utilitaire ─────────────────────────────────────────────────────────────

def post_csv(route, contenu_csv, nom_fichier="test.csv"):
    """Envoie une requête POST multipart avec un fichier CSV en mémoire."""
    return requests.post(
        f"{BASE_URL}{route}",
        files={"file": (nom_fichier, io.BytesIO(contenu_csv.encode("utf-8")), "text/csv")},
        timeout=5,
    )

def get(route):
    """Envoie une requête GET et retourne la réponse."""
    return requests.get(f"{BASE_URL}{route}", timeout=5)


# ─── CSV de test ─────────────────────────────────────────────────────────────

CSV_VALIDE = """\
nom_serie,valeur,categorie,date_mesure
serie_A,12.50,temperature,2024-01-15
serie_A,15.30,temperature,2024-01-16
serie_B,45.10,pression,2024-01-15
"""

CSV_DONNEES_EXEMPLE = """\
nom_serie,valeur,categorie,date_mesure
serie_A,12.50,temperature,2024-01-15
serie_A,15.30,temperature,2024-01-16
serie_A,8.70,temperature,2024-01-17
serie_A,21.00,temperature,2024-01-18
serie_A,13.20,temperature,2024-01-19
serie_A,9.80,temperature,2024-01-20
serie_A,17.60,temperature,2024-01-21
serie_A,11.40,temperature,2024-01-22
serie_B,45.10,pression,2024-01-15
serie_B,52.80,pression,2024-01-16
serie_B,48.60,pression,2024-01-17
serie_B,55.20,pression,2024-01-18
serie_B,50.90,pression,2024-01-19
serie_B,47.30,pression,2024-01-20
serie_B,53.70,pression,2024-01-21
serie_B,49.80,pression,2024-01-22
serie_C,220.5,debit,2024-01-15
serie_C,235.8,debit,2024-01-16
serie_C,198.2,debit,2024-01-17
serie_C,245.1,debit,2024-01-18
serie_C,210.9,debit,2024-01-19
serie_C,228.4,debit,2024-01-20
"""

CSV_SANS_COLONNE_VALEUR = """\
nom_serie,categorie,date_mesure
serie_X,temperature,2024-01-15
"""

CSV_SANS_COLONNE_NOM_SERIE = """\
valeur,categorie,date_mesure
12.5,temperature,2024-01-15
"""

CSV_VALEURS_INVALIDES = """\
nom_serie,valeur,categorie,date_mesure
serie_X,abc,temperature,2024-01-15
serie_X,12.5,temperature,2024-01-16
serie_X,,temperature,2024-01-17
"""

CSV_TOUTES_VALEURS_INVALIDES = """\
nom_serie,valeur,categorie,date_mesure
serie_X,abc,temperature,2024-01-15
serie_X,NaN_text,temperature,2024-01-16
"""

CSV_COLONNES_MINIMALES = """\
nom_serie,valeur
serie_Z,99.9
serie_Z,88.8
"""


# ─── Tests /upload/csv — cas nominaux ────────────────────────────────────────

class TestUploadCSVNominal(unittest.TestCase):

    def test_chargement_valide_retourne_201(self):
        """Un CSV valide doit retourner HTTP 201."""
        r = post_csv("/upload/csv", CSV_VALIDE)
        self.assertEqual(r.status_code, 201)

    def test_chargement_valide_statut_success(self):
        """La réponse doit contenir statut = 'success'."""
        r = post_csv("/upload/csv", CSV_VALIDE)
        self.assertEqual(r.status_code, 201)
        body = r.json()
        self.assertEqual(body["statut"], "success")

    def test_chargement_valide_champs_reponse(self):
        """La réponse doit contenir les champs attendus."""
        r = post_csv("/upload/csv", CSV_VALIDE)
        body = r.json()
        self.assertIn("statut", body)
        self.assertIn("lignes_inserees", body)
        self.assertIn("lignes_invalides_ignorees", body)
        self.assertIn("message", body)

    def test_chargement_donnees_exemple_22_lignes(self):
        """Le fichier donnees_exemple.csv doit insérer 22 lignes."""
        r = post_csv("/upload/csv", CSV_DONNEES_EXEMPLE, "donnees_exemple.csv")
        self.assertEqual(r.status_code, 201)
        body = r.json()
        self.assertEqual(body["lignes_inserees"], 22)
        self.assertEqual(body["lignes_invalides_ignorees"], 0)

    def test_colonnes_minimales_acceptees(self):
        """CSV avec seulement nom_serie et valeur doit être accepté."""
        r = post_csv("/upload/csv", CSV_COLONNES_MINIMALES)
        self.assertEqual(r.status_code, 201)
        self.assertEqual(r.json()["lignes_inserees"], 2)

    def test_valeurs_non_numeriques_ignorees(self):
        """Lignes avec valeur non numérique → ignorées, reste inséré."""
        r = post_csv("/upload/csv", CSV_VALEURS_INVALIDES)
        self.assertEqual(r.status_code, 201)
        body = r.json()
        self.assertEqual(body["lignes_inserees"], 1)
        self.assertEqual(body["lignes_invalides_ignorees"], 2)

    def test_content_type_reponse_json(self):
        """Le Content-Type de la réponse doit être application/json."""
        r = post_csv("/upload/csv", CSV_VALIDE)
        self.assertIn("application/json", r.headers.get("Content-Type", ""))


# ─── Tests /upload/csv — cas d'erreur ────────────────────────────────────────

class TestUploadCSVErreurs(unittest.TestCase):

    def test_sans_fichier_retourne_400(self):
        """Requête sans fichier → HTTP 400."""
        r = requests.post(f"{BASE_URL}/upload/csv", timeout=5)
        self.assertEqual(r.status_code, 400)
        self.assertIn("erreur", r.json())

    def test_fichier_non_csv_retourne_400(self):
        """Envoi d'un fichier .txt → HTTP 400."""
        r = requests.post(
            f"{BASE_URL}/upload/csv",
            files={"file": ("rapport.txt", io.BytesIO(b"ceci n'est pas un csv"), "text/plain")},
            timeout=5,
        )
        self.assertEqual(r.status_code, 400)
        self.assertIn("csv", r.json()["erreur"].lower())

    def test_colonne_valeur_manquante_retourne_400(self):
        """CSV sans colonne 'valeur' → HTTP 400 avec détail."""
        r = post_csv("/upload/csv", CSV_SANS_COLONNE_VALEUR)
        self.assertEqual(r.status_code, 400)
        body = r.json()
        self.assertIn("manquantes", body)
        self.assertIn("valeur", body["manquantes"])

    def test_colonne_nom_serie_manquante_retourne_400(self):
        """CSV sans colonne 'nom_serie' → HTTP 400."""
        r = post_csv("/upload/csv", CSV_SANS_COLONNE_NOM_SERIE)
        self.assertEqual(r.status_code, 400)
        self.assertIn("nom_serie", r.json()["manquantes"])

    def test_toutes_valeurs_invalides_retourne_400(self):
        """Si toutes les valeurs sont invalides → HTTP 400."""
        r = post_csv("/upload/csv", CSV_TOUTES_VALEURS_INVALIDES)
        self.assertEqual(r.status_code, 400)
        self.assertIn("erreur", r.json())

    def test_fichier_trop_volumineux_retourne_413(self):
        """Fichier > 5 Mo → HTTP 413."""
        gros = b"nom_serie,valeur\n" + b"A,1\n" * (5 * 1024 * 1024 // 4 + 1)
        r = requests.post(
            f"{BASE_URL}/upload/csv",
            files={"file": ("gros.csv", io.BytesIO(gros), "text/csv")},
            timeout=10,
        )
        self.assertEqual(r.status_code, 413)


# ─── Tests /upload/series ────────────────────────────────────────────────────

class TestUploadSeries(unittest.TestCase):

    def test_list_series_retourne_200(self):
        """GET /upload/series → HTTP 200."""
        r = get("/upload/series")
        self.assertEqual(r.status_code, 200)

    def test_list_series_corps_json_valide(self):
        """La réponse doit contenir 'series' (liste) et 'total' (entier)."""
        r = get("/upload/series")
        body = r.json()
        self.assertIn("series", body)
        self.assertIn("total", body)
        self.assertIsInstance(body["series"], list)
        self.assertIsInstance(body["total"], int)

    def test_list_series_total_coherent(self):
        """total doit correspondre au nombre d'éléments dans series."""
        r = get("/upload/series")
        body = r.json()
        self.assertEqual(body["total"], len(body["series"]))

    def test_list_series_structure_element(self):
        """Chaque série doit avoir les clés serie, n_points, debut, fin."""
        post_csv("/upload/csv", CSV_DONNEES_EXEMPLE, "donnees_exemple.csv")
        r = get("/upload/series")
        series = r.json()["series"]
        self.assertGreater(len(series), 0)
        s = series[0]
        self.assertIn("serie", s)
        self.assertIn("n_points", s)
        self.assertIn("debut", s)
        self.assertIn("fin", s)


# ─── Point d'entrée ──────────────────────────────────────────────────────────

if __name__ == "__main__":
    print("=" * 60)
    print("Tests unitaires — Service 4 : Chargement CSV vers MySQL")
    print(f"Cible : {BASE_URL}")
    print("=" * 60)
    unittest.main(verbosity=2)
