"""
Tests unitaires — Service 1 : Calculs Matriciels
Port : 5001

Les tests couvrent :
  - /matrices/add         (cas nominal + erreur dimensions)
  - /matrices/multiply    (cas nominal + dimensions incompatibles)
  - /matrices/transpose   (matrice rectangulaire)
  - /matrices/determinant (matrice carrée + matrice non carrée)
  - /matrices/inverse     (matrice inversible + matrice singulière)
"""

import unittest
import requests
import json

BASE_URL = "http://localhost:5001"


# ─── Utilitaire ─────────────────────────────────────────────────────────────

def post(route, payload):
    """Envoie une requête POST JSON et retourne la réponse."""
    return requests.post(
        f"{BASE_URL}{route}",
        headers={"Content-Type": "application/json"},
        data=json.dumps(payload),
        timeout=5,
    )


# ─── Tests /matrices/add ────────────────────────────────────────────────────

class TestMatricesAdd(unittest.TestCase):

    def test_add_2x2_nominal(self):
        """Addition classique de deux matrices 2×2."""
        r = post("/matrices/add", {"A": [[1, 2], [3, 4]], "B": [[5, 6], [7, 8]]})
        self.assertEqual(r.status_code, 200)
        body = r.json()
        self.assertEqual(body["operation"], "addition")
        self.assertEqual(body["resultat"], [[6.0, 8.0], [10.0, 12.0]])

    def test_add_3x3_nominal(self):
        """Addition de deux matrices 3×3."""
        A = [[1, 0, 0], [0, 1, 0], [0, 0, 1]]
        B = [[9, 8, 7], [6, 5, 4], [3, 2, 1]]
        r = post("/matrices/add", {"A": A, "B": B})
        self.assertEqual(r.status_code, 200)
        expected = [[10.0, 8.0, 7.0], [6.0, 6.0, 4.0], [3.0, 2.0, 2.0]]
        self.assertEqual(r.json()["resultat"], expected)

    def test_add_dimensions_incompatibles(self):
        """Addition de matrices de dimensions différentes → 400."""
        r = post("/matrices/add", {"A": [[1, 2]], "B": [[1, 2], [3, 4]]})
        self.assertEqual(r.status_code, 400)
        self.assertIn("erreur", r.json())

    def test_add_matrice_manquante(self):
        """Corps JSON incomplet (clé B absente) → 400."""
        r = post("/matrices/add", {"A": [[1, 2], [3, 4]]})
        self.assertEqual(r.status_code, 400)


# ─── Tests /matrices/multiply ───────────────────────────────────────────────

class TestMatricesMultiply(unittest.TestCase):

    def test_multiply_2x2_nominal(self):
        """Multiplication 2×2 × 2×2."""
        r = post("/matrices/multiply", {"A": [[1, 2], [3, 4]], "B": [[5, 6], [7, 8]]})
        self.assertEqual(r.status_code, 200)
        body = r.json()
        self.assertEqual(body["operation"], "multiplication")
        self.assertEqual(body["resultat"], [[19.0, 22.0], [43.0, 50.0]])

    def test_multiply_identite(self):
        """Multiplication par la matrice identité : A × I = A."""
        A = [[2, 3], [4, 5]]
        I = [[1, 0], [0, 1]]
        r = post("/matrices/multiply", {"A": A, "B": I})
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.json()["resultat"], [[2.0, 3.0], [4.0, 5.0]])

    def test_multiply_2x3_3x2(self):
        """Multiplication 2×3 × 3×2 → résultat 2×2."""
        A = [[1, 2, 3], [4, 5, 6]]
        B = [[7, 8], [9, 10], [11, 12]]
        r = post("/matrices/multiply", {"A": A, "B": B})
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.json()["resultat"], [[58.0, 64.0], [139.0, 154.0]])

    def test_multiply_dimensions_incompatibles(self):
        """Colonnes(A) ≠ Lignes(B) → 400."""
        r = post("/matrices/multiply", {"A": [[1, 2], [3, 4]], "B": [[1, 2, 3]]})
        self.assertEqual(r.status_code, 400)


# ─── Tests /matrices/transpose ──────────────────────────────────────────────

class TestMatricesTranspose(unittest.TestCase):

    def test_transpose_2x2(self):
        """Transposition d'une matrice 2×2."""
        r = post("/matrices/transpose", {"A": [[1, 2], [3, 4]]})
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.json()["operation"], "transposee")
        self.assertEqual(r.json()["resultat"], [[1.0, 3.0], [2.0, 4.0]])

    def test_transpose_rectangulaire(self):
        """Transposition d'une matrice 2×3 → doit donner 3×2."""
        A = [[1, 2, 3], [4, 5, 6]]
        r = post("/matrices/transpose", {"A": A})
        self.assertEqual(r.status_code, 200)
        expected = [[1.0, 4.0], [2.0, 5.0], [3.0, 6.0]]
        self.assertEqual(r.json()["resultat"], expected)

    def test_transpose_double_identite(self):
        """(A^T)^T = A."""
        A = [[1, 2, 3], [4, 5, 6]]
        r1 = post("/matrices/transpose", {"A": A})
        At = r1.json()["resultat"]
        r2 = post("/matrices/transpose", {"A": At})
        self.assertEqual(r2.json()["resultat"], [[1.0, 2.0, 3.0], [4.0, 5.0, 6.0]])


# ─── Tests /matrices/determinant ────────────────────────────────────────────

class TestMatricesDeterminant(unittest.TestCase):

    def test_determinant_2x2(self):
        """det([[1,2],[3,4]]) = 1×4 - 2×3 = -2."""
        r = post("/matrices/determinant", {"A": [[1, 2], [3, 4]]})
        self.assertEqual(r.status_code, 200)
        self.assertAlmostEqual(r.json()["resultat"], -2.0, places=4)

    def test_determinant_identite_3x3(self):
        """det(I₃) = 1."""
        I = [[1, 0, 0], [0, 1, 0], [0, 0, 1]]
        r = post("/matrices/determinant", {"A": I})
        self.assertEqual(r.status_code, 200)
        self.assertAlmostEqual(r.json()["resultat"], 1.0, places=4)

    def test_determinant_singuliere(self):
        """Matrice singulière → det ≈ 0 (pas d'erreur, juste 0)."""
        A = [[1, 2], [2, 4]]  # Lignes colinéaires → det = 0
        r = post("/matrices/determinant", {"A": A})
        self.assertEqual(r.status_code, 200)
        self.assertAlmostEqual(r.json()["resultat"], 0.0, places=4)

    def test_determinant_non_carree(self):
        """Matrice non carrée → 400."""
        r = post("/matrices/determinant", {"A": [[1, 2, 3], [4, 5, 6]]})
        self.assertEqual(r.status_code, 400)
        self.assertIn("erreur", r.json())


# ─── Tests /matrices/inverse ────────────────────────────────────────────────

class TestMatricesInverse(unittest.TestCase):

    def test_inverse_2x2_nominal(self):
        """Inverse de [[2,1],[5,3]] = [[3,-1],[-5,2]]."""
        r = post("/matrices/inverse", {"A": [[2, 1], [5, 3]]})
        self.assertEqual(r.status_code, 200)
        result = r.json()["resultat"]
        self.assertAlmostEqual(result[0][0],  3.0, places=4)
        self.assertAlmostEqual(result[0][1], -1.0, places=4)
        self.assertAlmostEqual(result[1][0], -5.0, places=4)
        self.assertAlmostEqual(result[1][1],  2.0, places=4)

    def test_inverse_produit_identite(self):
        """A × A⁻¹ doit donner la matrice identité (à ε près)."""
        import numpy as np
        A = [[4, 7], [2, 6]]
        r_inv = post("/matrices/inverse", {"A": A})
        self.assertEqual(r_inv.status_code, 200)
        A_inv = r_inv.json()["resultat"]
        produit = post("/matrices/multiply", {"A": A, "B": A_inv})
        res = produit.json()["resultat"]
        # Vérifier que le produit est proche de l'identité
        self.assertAlmostEqual(res[0][0], 1.0, places=3)
        self.assertAlmostEqual(res[0][1], 0.0, places=3)
        self.assertAlmostEqual(res[1][0], 0.0, places=3)
        self.assertAlmostEqual(res[1][1], 1.0, places=3)

    def test_inverse_singuliere(self):
        """Matrice singulière (det=0) → 400."""
        r = post("/matrices/inverse", {"A": [[1, 2], [2, 4]]})
        self.assertEqual(r.status_code, 400)
        self.assertIn("erreur", r.json())

    def test_inverse_non_carree(self):
        """Matrice non carrée → 400."""
        r = post("/matrices/inverse", {"A": [[1, 2, 3], [4, 5, 6]]})
        self.assertEqual(r.status_code, 400)


# ─── Point d'entrée ─────────────────────────────────────────────────────────

if __name__ == "__main__":
    print("=" * 60)
    print("Tests unitaires — Service 1 : Calculs Matriciels")
    print(f"Cible : {BASE_URL}")
    print("=" * 60)
    unittest.main(verbosity=2)