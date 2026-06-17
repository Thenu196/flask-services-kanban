from flask import Flask, request, jsonify
import numpy as np

app = Flask(__name__)

def parse_matrix(data, key):
    """Convertit une liste de listes en tableau NumPy."""
    try:
        return np.array(data[key], dtype=float)
    except (KeyError, ValueError) as e:
        raise ValueError(f"Matrice '{key}' invalide : {e}")

if __name__ == '__main__':
    app.run(debug=True, port=5001)
