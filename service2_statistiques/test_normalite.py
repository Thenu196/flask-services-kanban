"""
Tests unitaires — POST /stats/test_normalite
Lancer : python test_normalite.py
Dépendances : requests  (pip install requests)
Le serveur Flask doit tourner sur localhost:5002 avant l'exécution.
"""

import unittest
import requests

BASE_URL = "http://127.0.0.1:5002"
ENDPOINT = f"{BASE_URL}/stats/test_normalite"


def post(payload: dict) -> tuple[int, dict]:
    """Envoie une requête POST et retourne (status_code, json)."""
    r = requests.post(ENDPOINT, json=payload, timeout=5)
    return r.status_code, r.json()


class TestNormaliteRoute(unittest.TestCase):

    # ------------------------------------------------------------------ #
    # Cas nominaux                                                         #
    # ------------------------------------------------------------------ #

    def test_reponse_contient_operation_et_resultat(self):
        """La réponse doit avoir les clés 'operation' et 'resultat'."""
        status, data = post({"data": [2.1, 2.5, 2.3, 2.8, 2.4, 2.6, 2.2, 2.9, 2.7, 2.5]})
        self.assertEqual(status, 200)
        self.assertIn("operation", data)
        self.assertIn("resultat", data)
        self.assertEqual(data["operation"], "test_normalite_shapiro_wilk")

    def test_cles_resultat_completes(self):
        """Le résultat doit contenir statistique, p_value, est_normale, interpretation."""
        _, data = post({"data": [2.1, 2.5, 2.3, 2.8, 2.4, 2.6, 2.2, 2.9, 2.7, 2.5]})
        cles = {"statistique", "p_value", "est_normale", "interpretation"}
        self.assertTrue(cles.issubset(data["resultat"].keys()))

    def test_distribution_normale(self):
        """Une distribution quasi-normale doit retourner est_normale = True."""
        _, data = post({
            "data": [2.1, 2.5, 2.3, 2.8, 2.4, 2.6, 2.2, 2.9, 2.7, 2.5,
                     2.4, 2.6, 2.3, 2.5, 2.7, 2.4, 2.5, 2.6, 2.3, 2.5]
        })
        r = data["resultat"]
        self.assertTrue(r["est_normale"])
        self.assertIn("normale", r["interpretation"].lower())

    def test_distribution_non_normale(self):
        """Une distribution très asymétrique doit retourner est_normale = False."""
        _, data = post({
            "data": [1, 1, 1, 1, 2, 10, 20, 50, 100, 200, 500, 1000, 2000, 5000, 9000]
        })
        r = data["resultat"]
        self.assertFalse(r["est_normale"])
        self.assertIn("non normale", r["interpretation"].lower())

    def test_statistique_entre_0_et_1(self):
        """La statistique W de Shapiro-Wilk doit être entre 0 et 1."""
        _, data = post({"data": [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]})
        stat = data["resultat"]["statistique"]
        self.assertGreaterEqual(stat, 0.0)
        self.assertLessEqual(stat, 1.0)

    def test_p_value_entre_0_et_1(self):
        """La p-value doit être comprise entre 0 et 1."""
        _, data = post({"data": [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]})
        p = data["resultat"]["p_value"]
        self.assertGreaterEqual(p, 0.0)
        self.assertLessEqual(p, 1.0)

    def test_est_normale_est_booleen(self):
        """Le champ 'est_normale' doit être un booléen."""
        _, data = post({"data": [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]})
        self.assertIsInstance(data["resultat"]["est_normale"], bool)

    def test_interpretation_coherente_avec_p_value(self):
        """L'interprétation doit être cohérente avec la p-value et est_normale."""
        _, data = post({"data": [2.1, 2.5, 2.3, 2.8, 2.4, 2.6, 2.2, 2.9, 2.7, 2.5]})
        r = data["resultat"]
        if r["p_value"] > 0.05:
            self.assertTrue(r["est_normale"])
            self.assertIn("normale (p > 0.05)", r["interpretation"])
        else:
            self.assertFalse(r["est_normale"])
            self.assertIn("non normale (p <= 0.05)", r["interpretation"])

    def test_valeurs_decimales_acceptees(self):
        """La route doit accepter des valeurs décimales."""
        status, data = post({
            "data": [1.1, 2.2, 3.3, 4.4, 5.5, 6.6, 7.7, 8.8, 9.9, 10.0]
        })
        self.assertEqual(status, 200)
        self.assertIn("resultat", data)

    def test_valeurs_negatives_acceptees(self):
        """La route doit accepter des valeurs négatives."""
        status, data = post({
            "data": [-5, -3, -1, 0, 1, 3, 5, -2, 2, -4]
        })
        self.assertEqual(status, 200)
        self.assertIn("resultat", data)

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
        status, data = post({"valeurs": [1, 2, 3, 4, 5]})
        self.assertEqual(status, 400)
        self.assertIn("erreur", data)

    def test_erreur_plus_de_5000_valeurs(self):
        """Une liste de plus de 5000 valeurs doit retourner 400."""
        status, data = post({"data": list(range(5001))})
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