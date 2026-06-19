"""
Tests unitaires — POST /stats/correlation
Lancer : python test_correlation.py
Dépendances : requests  (pip install requests)
Le serveur Flask doit tourner sur localhost:5002 avant l'exécution.
"""

import unittest
import requests

BASE_URL = "http://127.0.0.1:5002"
ENDPOINT = f"{BASE_URL}/stats/correlation"


def post(payload: dict) -> tuple[int, dict]:
    """Envoie une requête POST et retourne (status_code, json)."""
    r = requests.post(ENDPOINT, json=payload, timeout=5)
    return r.status_code, r.json()


class TestCorrelationRoute(unittest.TestCase):

    # ------------------------------------------------------------------ #
    # Cas nominaux                                                         #
    # ------------------------------------------------------------------ #

    def test_reponse_contient_operation_et_resultat(self):
        """La réponse doit avoir les clés 'operation' et 'resultat'."""
        status, data = post({
            "x": [1, 2, 3, 4, 5],
            "y": [2, 4, 5, 4, 5]
        })
        self.assertEqual(status, 200)
        self.assertIn("operation", data)
        self.assertIn("resultat", data)
        self.assertEqual(data["operation"], "correlation_pearson")

    def test_cles_resultat_completes(self):
        """Le résultat doit contenir r, p_value, interpretation, significatif."""
        _, data = post({
            "x": [1, 2, 3, 4, 5],
            "y": [2, 4, 5, 4, 5]
        })
        cles = {"r", "p_value", "interpretation", "significatif"}
        self.assertTrue(cles.issubset(data["resultat"].keys()))

    def test_correlation_forte_positive(self):
        """Une relation linéaire parfaite doit donner r ≈ 1 et interprétation 'forte'."""
        _, data = post({
            "x": [1, 2, 3, 4, 5, 6, 7, 8, 9, 10],
            "y": [2, 4, 6, 8, 10, 12, 14, 16, 18, 20]
        })
        r = data["resultat"]
        self.assertAlmostEqual(r["r"], 1.0, places=3)
        self.assertEqual(r["interpretation"], "forte")
        self.assertTrue(r["significatif"])

    def test_correlation_forte_negative(self):
        """Une relation inversement proportionnelle doit donner r ≈ −1."""
        _, data = post({
            "x": [1, 2, 3, 4, 5, 6, 7, 8, 9, 10],
            "y": [10, 9, 8, 7, 6, 5, 4, 3, 2, 1]
        })
        r = data["resultat"]
        self.assertAlmostEqual(r["r"], -1.0, places=3)
        self.assertEqual(r["interpretation"], "forte")

    def test_correlation_faible(self):
        """Des séries non corrélées doivent donner une interprétation 'faible'."""
        _, data = post({
            "x": [1, 2, 3, 4, 5, 6, 7, 8, 9, 10],
            "y": [5, 1, 9, 3, 7, 2, 8, 4, 6, 10]
        })
        r = data["resultat"]
        self.assertIn(r["interpretation"], ["faible", "modérée"])

    def test_r_entre_moins1_et_1(self):
        """Le coefficient r doit toujours être compris entre −1 et 1."""
        _, data = post({
            "x": [10, 20, 30, 40, 50],
            "y": [15, 25, 35, 45, 55]
        })
        r_val = data["resultat"]["r"]
        self.assertGreaterEqual(r_val, -1.0)
        self.assertLessEqual(r_val, 1.0)

    def test_p_value_positive(self):
        """La p-value doit toujours être positive."""
        _, data = post({
            "x": [1, 2, 3, 4, 5],
            "y": [2, 4, 5, 4, 5]
        })
        self.assertGreaterEqual(data["resultat"]["p_value"], 0.0)

    def test_significatif_est_booleen(self):
        """Le champ 'significatif' doit être un booléen."""
        _, data = post({
            "x": [1, 2, 3, 4, 5],
            "y": [2, 4, 5, 4, 5]
        })
        self.assertIsInstance(data["resultat"]["significatif"], bool)

    # ------------------------------------------------------------------ #
    # Cas d'erreur                                                         #
    # ------------------------------------------------------------------ #

    def test_erreur_longueurs_differentes(self):
        """x et y de longueurs différentes doivent retourner 400."""
        status, data = post({
            "x": [1, 2, 3, 4, 5],
            "y": [1, 2, 3]
        })
        self.assertEqual(status, 400)
        self.assertIn("erreur", data)

    def test_erreur_cle_x_manquante(self):
        """L'absence de la clé 'x' doit retourner 400."""
        status, data = post({"y": [1, 2, 3, 4, 5]})
        self.assertEqual(status, 400)
        self.assertIn("erreur", data)

    def test_erreur_cle_y_manquante(self):
        """L'absence de la clé 'y' doit retourner 400."""
        status, data = post({"x": [1, 2, 3, 4, 5]})
        self.assertEqual(status, 400)
        self.assertIn("erreur", data)

    def test_erreur_liste_trop_courte(self):
        """Une liste d'un seul élément doit retourner 400."""
        status, data = post({"x": [1], "y": [2]})
        self.assertEqual(status, 400)
        self.assertIn("erreur", data)

    def test_erreur_corps_vide(self):
        """Un corps de requête vide doit retourner 400."""
        r = requests.post(
            ENDPOINT,
            data="",
            headers={"Content-Type": "application/json"},
            timeout=5
        )
        self.assertEqual(r.status_code, 400)


if __name__ == "__main__":
    unittest.main(verbosity=2)