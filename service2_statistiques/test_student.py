"""
Tests unitaires — POST /stats/test_student
Lancer : python test_student.py
Dépendances : requests  (pip install requests)
Le serveur Flask doit tourner sur localhost:5002 avant l'exécution.
"""

import unittest
import requests

BASE_URL = "http://127.0.0.1:5002"
ENDPOINT = f"{BASE_URL}/stats/test_student"


def post(payload: dict) -> tuple[int, dict]:
    """Envoie une requête POST et retourne (status_code, json)."""
    r = requests.post(ENDPOINT, json=payload, timeout=5)
    return r.status_code, r.json()


class TestStudentRoute(unittest.TestCase):

    # ------------------------------------------------------------------ #
    # Cas nominaux                                                         #
    # ------------------------------------------------------------------ #

    def test_reponse_contient_operation_et_resultat(self):
        """La réponse doit avoir les clés 'operation' et 'resultat'."""
        status, data = post({
            "groupe1": [20, 22, 19, 24, 21],
            "groupe2": [28, 30, 27, 32, 29]
        })
        self.assertEqual(status, 200)
        self.assertIn("operation", data)
        self.assertIn("resultat", data)
        self.assertEqual(data["operation"], "test_t_student")

    def test_cles_resultat_completes(self):
        """Le résultat doit contenir t_statistique, p_value, difference_significative."""
        _, data = post({
            "groupe1": [20, 22, 19, 24, 21],
            "groupe2": [28, 30, 27, 32, 29]
        })
        cles = {"t_statistique", "p_value", "difference_significative"}
        self.assertTrue(cles.issubset(data["resultat"].keys()))

    def test_difference_significative(self):
        """Deux groupes très différents doivent donner difference_significative = True."""
        _, data = post({
            "groupe1": [20, 22, 19, 24, 21, 23, 20, 25, 22, 21],
            "groupe2": [28, 30, 27, 32, 29, 31, 28, 33, 30, 29]
        })
        r = data["resultat"]
        self.assertTrue(r["difference_significative"])
        self.assertLess(r["p_value"], 0.05)

    def test_difference_non_significative(self):
        """Deux groupes très proches doivent donner difference_significative = False."""
        _, data = post({
            "groupe1": [20, 22, 19, 24, 21, 23, 20, 25, 22, 21],
            "groupe2": [21, 23, 20, 25, 22, 24, 21, 26, 23, 22]
        })
        r = data["resultat"]
        self.assertFalse(r["difference_significative"])
        self.assertGreaterEqual(r["p_value"], 0.05)

    def test_p_value_entre_0_et_1(self):
        """La p-value doit être comprise entre 0 et 1."""
        _, data = post({
            "groupe1": [1, 2, 3, 4, 5],
            "groupe2": [6, 7, 8, 9, 10]
        })
        p = data["resultat"]["p_value"]
        self.assertGreaterEqual(p, 0.0)
        self.assertLessEqual(p, 1.0)

    def test_difference_significative_est_booleen(self):
        """Le champ 'difference_significative' doit être un booléen."""
        _, data = post({
            "groupe1": [1, 2, 3, 4, 5],
            "groupe2": [6, 7, 8, 9, 10]
        })
        self.assertIsInstance(data["resultat"]["difference_significative"], bool)

    def test_t_statistique_est_nombre(self):
        """La statistique t doit être un nombre (positif ou négatif)."""
        _, data = post({
            "groupe1": [1, 2, 3, 4, 5],
            "groupe2": [6, 7, 8, 9, 10]
        })
        t = data["resultat"]["t_statistique"]
        self.assertIsInstance(t, float)

    def test_groupes_tailles_differentes(self):
        """Les deux groupes peuvent avoir des tailles différentes."""
        status, data = post({
            "groupe1": [1, 2, 3],
            "groupe2": [10, 20, 30, 40, 50]
        })
        self.assertEqual(status, 200)
        self.assertIn("resultat", data)

    def test_valeurs_decimales(self):
        """La route doit accepter des valeurs décimales."""
        status, data = post({
            "groupe1": [1.1, 2.2, 3.3, 4.4, 5.5],
            "groupe2": [6.6, 7.7, 8.8, 9.9, 10.0]
        })
        self.assertEqual(status, 200)
        self.assertIn("resultat", data)

    def test_valeurs_negatives(self):
        """La route doit accepter des valeurs négatives."""
        status, data = post({
            "groupe1": [-5, -3, -1, -2, -4],
            "groupe2": [1, 3, 5, 2, 4]
        })
        self.assertEqual(status, 200)
        self.assertIn("resultat", data)

    # ------------------------------------------------------------------ #
    # Cas d'erreur                                                         #
    # ------------------------------------------------------------------ #

    def test_erreur_groupe1_trop_court(self):
        """Un groupe1 d'un seul élément doit retourner 400."""
        status, data = post({
            "groupe1": [42],
            "groupe2": [1, 2, 3, 4, 5]
        })
        self.assertEqual(status, 400)
        self.assertIn("erreur", data)

    def test_erreur_groupe2_trop_court(self):
        """Un groupe2 d'un seul élément doit retourner 400."""
        status, data = post({
            "groupe1": [1, 2, 3, 4, 5],
            "groupe2": [42]
        })
        self.assertEqual(status, 400)
        self.assertIn("erreur", data)

    def test_erreur_cle_groupe1_manquante(self):
        """L'absence de la clé 'groupe1' doit retourner 400."""
        status, data = post({"groupe2": [1, 2, 3, 4, 5]})
        self.assertEqual(status, 400)
        self.assertIn("erreur", data)

    def test_erreur_cle_groupe2_manquante(self):
        """L'absence de la clé 'groupe2' doit retourner 400."""
        status, data = post({"groupe1": [1, 2, 3, 4, 5]})
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