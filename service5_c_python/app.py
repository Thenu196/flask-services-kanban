# app.py — Service 5 : fonctions C appelées depuis Python via ctypes

from flask import Flask, request, jsonify
import c_bridge as C

app = Flask(__name__)


def validate_list(data, key, min_len=1):
    """Valide qu'une clé JSON contient une liste de nombres."""
    if key not in data:
        raise ValueError(f"Clé '{key}' manquante dans la requête")

    values = data[key]

    if not isinstance(values, list) or len(values) < min_len:
        raise ValueError(f"'{key}' doit être une liste d'au moins {min_len} valeur(s)")

    return [float(v) for v in values]  # Forcer le type float


# ─── Route 1 : Statistiques descriptives ──────────────────────────
@app.route('/c/stats/describe', methods=['POST'])
def c_describe():
    data = request.get_json()
    try:
        values = validate_list(data, 'data', min_len=2)

        result = {
            'n': len(values),
            'moyenne': C.moyenne(values),
            'mediane': C.mediane(values),
            'ecart_type': C.ecart_type(values),
            'variance': C.variance(values),
            'minimum': C.minimum(values),
            'maximum': C.maximum(values),
        }

        return jsonify({
            'moteur': 'C/ctypes',
            'operation': 'description',
            'resultat': result
        })

    except (ValueError, TypeError) as e:
        return jsonify({'erreur': str(e)}), 400


# ─── Route 2 : Moyenne ────────────────────────────────────────────
@app.route('/c/stats/mean', methods=['POST'])
def c_mean():
    data = request.get_json()
    try:
        values = validate_list(data, 'data')

        return jsonify({
            'moteur': 'C/ctypes',
            'operation': 'moyenne',
            'resultat': C.moyenne(values)
        })

    except (ValueError, TypeError) as e:
        return jsonify({'erreur': str(e)}), 400


# ─── Route 3 : Écart-type ─────────────────────────────────────────
@app.route('/c/stats/stddev', methods=['POST'])
def c_stddev():
    data = request.get_json()
    try:
        values = validate_list(data, 'data', min_len=2)

        return jsonify({
            'moteur': 'C/ctypes',
            'operation': 'ecart_type',
            'resultat': C.ecart_type(values)
        })

    except (ValueError, TypeError) as e:
        return jsonify({'erreur': str(e)}), 400


# ─── Route 4 : Médiane ────────────────────────────────────────────
@app.route('/c/stats/median', methods=['POST'])
def c_median():
    data = request.get_json()
    try:
        values = validate_list(data, 'data')

        return jsonify({
            'moteur': 'C/ctypes',
            'operation': 'mediane',
            'resultat': C.mediane(values)
        })

    except (ValueError, TypeError) as e:
        return jsonify({'erreur': str(e)}), 400


# ─── Route 5 : Produit scalaire ───────────────────────────────────
@app.route('/c/stats/dot', methods=['POST'])
def c_dot():
    data = request.get_json()
    try:
        v1 = validate_list(data, 'v1')
        v2 = validate_list(data, 'v2')

        if len(v1) != len(v2):
            return jsonify({'erreur': 'v1 et v2 doivent avoir la même longueur'}), 400

        return jsonify({
            'moteur': 'C/ctypes',
            'operation': 'produit_scalaire',
            'resultat': C.dot_product(v1, v2)
        })

    except (ValueError, TypeError) as e:
        return jsonify({'erreur': str(e)}), 400


# ─── Route 6 : Vérification de santé ──────────────────────────────
@app.route('/c/health', methods=['GET'])
def health():
    return jsonify({
        'statut': 'ok',
        'service': 'Service 5 — C/Python Bridge',
        'port': 5005,
        'bibliotheque': 'lib/stats.so',
        'routes': [
            'POST /c/stats/describe',
            'POST /c/stats/mean',
            'POST /c/stats/stddev',
            'POST /c/stats/median',
            'POST /c/stats/dot',
        ]
    })


if __name__ == '__main__':
    app.run(debug=True, port=5005)