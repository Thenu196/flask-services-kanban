import json
from urllib import request
from urllib.error import HTTPError

BASE_URL = "http://127.0.0.1:5003"


def get_json(path):
    url = BASE_URL + path

    try:
        with request.urlopen(url) as response:
            data = json.loads(response.read().decode("utf-8"))
            return response.status, data

    except HTTPError as error:
        data = json.loads(error.read().decode("utf-8"))
        return error.code, data


def test_describe_ok():
    status, data = get_json("/db/stats/describe?serie=serie_A")

    assert status == 200
    assert data["source"] == "mysql"
    assert data["resultat"]["serie"] == "serie_A"
    assert "moyenne" in data["resultat"]
    assert "mediane" in data["resultat"]
    assert "ecart_type" in data["resultat"]

    print("Test describe OK")


def test_correlation_ok():
    status, data = get_json(
        "/db/stats/correlation?serie_x=serie_A&serie_y=serie_B"
    )

    assert status == 200
    assert data["source"] == "mysql"
    assert data["series"]["x"] == "serie_A"
    assert data["series"]["y"] == "serie_B"
    assert "r" in data["resultat"]
    assert "p_value" in data["resultat"]
    assert "significatif" in data["resultat"]

    print("Test correlation OK")


def test_describe_param_manquant():
    status, data = get_json("/db/stats/describe")

    assert status == 400
    assert "erreur" in data

    print("Test paramètre manquant OK")


def test_correlation_param_manquant():
    status, data = get_json("/db/stats/correlation")

    assert status == 400
    assert "erreur" in data

    print("Test paramètres correlation manquants OK")


def test_serie_inexistante():
    status, data = get_json("/db/stats/describe?serie=serie_X")

    assert status == 404
    assert "erreur" in data

    print("Test série inexistante OK")


if __name__ == "__main__":
    test_describe_ok()
    test_correlation_ok()
    test_describe_param_manquant()
    test_correlation_param_manquant()
    test_serie_inexistante()

    print("Tous les tests client Python sont passés.")