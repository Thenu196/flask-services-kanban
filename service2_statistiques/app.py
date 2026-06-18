from flask import Flask, request, jsonify
import numpy as np
from scipy import stats

app = Flask(__name__)

#Structure de base 
def validate_data(data, key='data'):
    if key not in data:
        raise ValueError(f"Clé '{key}' manquante dans la requête")
    values = data[key]
    if not isinstance(values, list) or len(values) < 2:
        raise ValueError("'data' doit être une liste d'au moins 2 valeurs")
    return np.array(values, dtype=float)

# Route 1 - Description statistique : POST /stats/describe 

@app.route('/stats/describe', methods=['POST'])
def describe():
    data = request.get_json()

    try:
        values = validate_data(data)

        result = {
            'n': int(len(values)),
            'moyenne': round(float(np.mean(values)), 4),
            'mediane': round(float(np.median(values)), 4),
            'ecart_type': round(float(np.std(values, ddof=1)), 4),
            'variance': round(float(np.var(values, ddof=1)), 4),
            'minimum': round(float(np.min(values)), 4),
            'maximum': round(float(np.max(values)), 4),
            'q1': round(float(np.percentile(values, 25)), 4),
            'q3': round(float(np.percentile(values, 75)), 4),
            'etendue': round(float(np.ptp(values)), 4),
        }

        return jsonify({
            'operation': 'description',
            'resultat': result
        })

    except (ValueError, TypeError) as e:
        return jsonify({
            'erreur': str(e)
        }), 400


if __name__ == '__main__':
    app.run(debug=True, port=5002)
