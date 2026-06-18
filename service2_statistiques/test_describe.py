"""
Tests unitaires — POST /stats/describe
Lancer : python test_describe.py
Dépendances : requests  (pip install requests)
Le serveur Flask doit tourner sur localhost:5002 avant l'exécution.
"""

import unittest
import requests

BASE_URL = "http://localhost:5002"
ENDPOINT = f"{BASE_URL}/stats/describe"


def post(payload: dict) -> tuple[int, dict]:
    """Envoie une requête POST et retourne (status_code, json)."""
    r = requests.post(ENDPOINT, json=payload, timeout=5)
    return r.status_code, r.json()


class TestDescribeRoute(unittest.TestCase):

    # ------------------------------------------------------------------ #
    # Cas nominaux                                                         #
    # ------------------------------------------------------------------ #

    def test_reponse_contient_operation_et_resultat(self):
        """La réponse doit avoir les clés 'operation' et 'resultat'."""
        status, data = post({"data": [1, 2, 3, 4, 5]})
        self.assertEqual(status, 200)
        self.assertIn("operation", data)
        self.assertIn("resultat", data)
        self.assertEqual(data["operation"], "description")

    def test_cles_resultat_completes(self):
        """Le résultat doit contenir les 10 métriques attendues."""
        cles_attendues = {
            "n", "moyenne", "mediane", "ecart_type",
            "variance", "minimum", "maximum", "q1", "q3", "etendue"
        }
        _, data = post({"data": [10, 20, 30, 40, 50]})
        self.assertTrue(cles_attendues.issubset(data["resultat"].keys()))

    def test_valeurs_correctes_liste_simple(self):
        """Vérifie les valeurs exactes sur [2, 4, 4, 4, 5, 5, 7, 9]."""
        _, data = post({"data": [2, 4, 4, 4, 5, 5, 7, 9]})
        r = data["resultat"]
        self.assertEqual(r["n"],        8)
        self.assertAlmostEqual(r["moyenne"],    5.0,   places=3)
        self.assertAlmostEqual(r["mediane"],    4.5,   places=3)
        self.assertAlmostEqual(r["minimum"],    2.0,   places=3)
        self.assertAlmostEqual(r["maximum"],    9.0,   places=3)
        self.assertAlmostEqual(r["etendue"],    7.0,   places=3)

    def test_valeurs_decimales(self):
        """La route accepte et traite correctement les flottants."""
        status, data = post({"data": [12.5, 15.3, 8.7, 21.0, 13.2, 9.8, 17.6, 11.4]})
        self.assertEqual(status, 200)
        r = data["resultat"]
        self.assertEqual(r["n"], 8)
        self.assertAlmostEqual(r["minimum"], 8.7,  places=3)
        self.assertAlmostEqual(r["maximum"], 21.0, places=3)

    def test_deux_valeurs_minimum(self):
        """La liste minimale de 2 éléments doit fonctionner."""
        status, data = post({"data": [3.0, 7.0]})
        self.assertEqual(status, 200)
        self.assertIn("resultat", data)

    def test_valeurs_negatives(self):
        """Les valeurs négatives doivent être acceptées."""
        status, data = post({"data": [-5, -3, -1, 0, 2, 4]})
        self.assertEqual(status, 200)
        r = data["resultat"]
        self.assertAlmostEqual(r["minimum"], -5.0, places=3)
        self.assertAlmostEqual(r["maximum"],  4.0, places=3)

    def test_grande_liste(self):
        """La route doit gérer une liste de 1000 éléments."""
        import random
        data = [round(random.uniform(0, 100), 2) for _ in range(1000)]
        status, resp = post({"data": data})
        self.assertEqual(status, 200)
        self.assertEqual(resp["resultat"]["n"], 1000)

    # ------------------------------------------------------------------ #
    # Cas d'erreur                                                         #
    # ------------------------------------------------------------------ #

    def test_erreur_liste_trop_courte(self):
        """Une liste d'un seul élément doit retourner 400."""
        status, data = post({"data": [42]})
        self.assertEqual(status, 400)
        self.assertIn("erreur", data)

    def test_erreur_liste_vide(self):
        """Une liste vide doit retourner 400."""
        status, data = post({"data": []})
        self.assertEqual(status, 400)
        self.assertIn("erreur", data)

    def test_erreur_cle_manquante(self):
        """L'absence de la clé 'data' doit retourner 400."""
        status, data = post({"valeurs": [1, 2, 3]})
        self.assertEqual(status, 400)
        self.assertIn("erreur", data)

    def test_erreur_data_non_liste(self):
        """Passer un scalaire au lieu d'une liste doit retourner 400."""
        status, data = post({"data": 42})
        self.assertEqual(status, 400)
        self.assertIn("erreur", data)

    def test_erreur_corps_vide(self):
        """Un corps de requête vide doit retourner 400."""
        r = requests.post(ENDPOINT, data="", headers={"Content-Type": "application/json"}, timeout=5)
        self.assertEqual(r.status_code, 400)


if __name__ == "__main__":
    unittest.main(verbosity=2)