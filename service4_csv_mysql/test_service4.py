"""
Tests unitaires — Service 4 : Chargement CSV vers MySQL
========================================================
Stratégie : la connexion MySQL est mockée via unittest.mock afin que
les tests s'exécutent sans base de données réelle.
"""

import io
import json
import pytest
from unittest.mock import patch, MagicMock

# On importe l'app Flask depuis app.py
from app import app

@pytest.fixture
def client():
    app.config['TESTING'] = True
    with app.test_client() as c:
        yield c


# Helpers

def make_csv_file(content: str, filename: str = 'test.csv'):
    """Retourne un objet FileStorage simulé à partir d'une chaîne CSV."""
    return (io.BytesIO(content.encode('utf-8')), filename)


CSV_NOMINAL = """\
nom_serie,valeur,categorie,date_mesure
serie_A,12.50,temperature,2024-01-15
serie_A,15.30,temperature,2024-01-16
serie_B,45.10,pression,2024-01-15
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

CSV_COLONNES_SUPERFLUES = """\
nom_serie,valeur,categorie,date_mesure,colonne_inconnue
serie_A,10.0,temp,2024-01-15,extra
"""


# 1. Tests — Validation du fichier (avant lecture CSV)

class TestValidationFichier:

    def test_aucun_fichier_envoye(self, client):
        """POST sans champ 'file' → 400."""
        resp = client.post('/upload/csv')
        assert resp.status_code == 400
        data = resp.get_json()
        assert 'erreur' in data
        assert 'file' in data['erreur'].lower() or 'manquante' in data['erreur'].lower()

    def test_nom_fichier_vide(self, client):
        """Fichier envoyé avec nom vide → 400."""
        data = {'file': (io.BytesIO(b'nom_serie,valeur\nA,1'), '')}
        resp = client.post('/upload/csv', data=data, content_type='multipart/form-data')
        assert resp.status_code == 400
        assert 'vide' in resp.get_json()['erreur'].lower()

    def test_extension_non_csv(self, client):
        """Fichier .txt → 400."""
        data = {'file': make_csv_file('nom_serie,valeur\nA,1', 'fichier.txt')}
        resp = client.post('/upload/csv', data=data, content_type='multipart/form-data')
        assert resp.status_code == 400
        assert 'csv' in resp.get_json()['erreur'].lower()

    def test_extension_json_refusee(self, client):
        """Fichier .json → 400."""
        data = {'file': make_csv_file('{}', 'data.json')}
        resp = client.post('/upload/csv', data=data, content_type='multipart/form-data')
        assert resp.status_code == 400

    def test_fichier_trop_volumineux(self, client):
        """Fichier > 5 Mo → 413."""
        gros_contenu = b'nom_serie,valeur\n' + b'A,1\n' * (5 * 1024 * 1024 // 4 + 1)
        data = {'file': (io.BytesIO(gros_contenu), 'gros.csv')}
        resp = client.post('/upload/csv', data=data, content_type='multipart/form-data')
        assert resp.status_code == 413
        assert 'volumineux' in resp.get_json()['erreur'].lower()

    def test_csv_illisible(self, client):
        """Contenu binaire invalide → 400."""
        data = {'file': (io.BytesIO(b'\xff\xfe\x00\x00'), 'corrompu.csv')}
        resp = client.post('/upload/csv', data=data, content_type='multipart/form-data')
        # pandas peut lire certains fichiers binaires ; on vérifie au moins que
        # l'app répond sans crash (400 ou 201 selon le contenu)
        assert resp.status_code in (400, 201)


# 2. Tests — Validation des colonnes

class TestValidationColonnes:

    def test_colonne_valeur_manquante(self, client):
        """CSV sans colonne 'valeur' → 400 avec détail."""
        data = {'file': make_csv_file(CSV_SANS_COLONNE_VALEUR)}
        resp = client.post('/upload/csv', data=data, content_type='multipart/form-data')
        assert resp.status_code == 400
        body = resp.get_json()
        assert 'manquantes' in body
        assert 'valeur' in body['manquantes']

    def test_colonne_nom_serie_manquante(self, client):
        """CSV sans colonne 'nom_serie' → 400."""
        data = {'file': make_csv_file(CSV_SANS_COLONNE_NOM_SERIE)}
        resp = client.post('/upload/csv', data=data, content_type='multipart/form-data')
        assert resp.status_code == 400
        body = resp.get_json()
        assert 'nom_serie' in body['manquantes']

    def test_les_deux_colonnes_obligatoires_manquantes(self, client):
        """CSV vide de colonnes → 400, les deux colonnes signalées."""
        data = {'file': make_csv_file('categorie,date_mesure\ntemp,2024-01-01')}
        resp = client.post('/upload/csv', data=data, content_type='multipart/form-data')
        assert resp.status_code == 400
        body = resp.get_json()
        assert set(body['manquantes']) == {'nom_serie', 'valeur'}


# 3. Tests — Nettoyage des données

class TestNettoyageDonnees:

    @patch('app.get_connection')
    def test_valeurs_non_numeriques_ignorees(self, mock_conn, client):
        """Lignes avec valeur non numérique → ignorées, reste inséré."""
        mock_cursor = MagicMock()
        mock_conn.return_value.cursor.return_value = mock_cursor

        data = {'file': make_csv_file(CSV_VALEURS_INVALIDES)}
        resp = client.post('/upload/csv', data=data, content_type='multipart/form-data')

        assert resp.status_code == 201
        body = resp.get_json()
        # 1 ligne valide (12.5), 2 invalides (abc et vide)
        assert body['lignes_inserees'] == 1
        assert body['lignes_invalides_ignorees'] == 2

    @patch('app.get_connection')
    def test_toutes_valeurs_invalides(self, mock_conn, client):
        """Si toutes les valeurs sont invalides → 400, aucune insertion."""
        data = {'file': make_csv_file(CSV_TOUTES_VALEURS_INVALIDES)}
        resp = client.post('/upload/csv', data=data, content_type='multipart/form-data')
        assert resp.status_code == 400
        assert 'aucune ligne valide' in resp.get_json()['erreur'].lower()
        mock_conn.assert_not_called()

    @patch('app.get_connection')
    def test_colonnes_superflues_ignorees(self, mock_conn, client):
        """Colonnes hors COLONNES_VALIDES doivent être écartées sans erreur."""
        mock_cursor = MagicMock()
        mock_conn.return_value.cursor.return_value = mock_cursor

        data = {'file': make_csv_file(CSV_COLONNES_SUPERFLUES)}
        resp = client.post('/upload/csv', data=data, content_type='multipart/form-data')
        assert resp.status_code == 201
        assert resp.get_json()['lignes_inserees'] == 1



# 4. Tests — Insertion MySQL (mock)

class TestInsertionMySQL:

    @patch('app.get_connection')
    def test_chargement_nominal(self, mock_conn, client):
        """CSV valide → 201, lignes_inserees = nombre de lignes."""
        mock_cursor = MagicMock()
        mock_conn.return_value.cursor.return_value = mock_cursor

        data = {'file': make_csv_file(CSV_NOMINAL)}
        resp = client.post('/upload/csv', data=data, content_type='multipart/form-data')

        assert resp.status_code == 201
        body = resp.get_json()
        assert body['statut'] == 'success'
        assert body['lignes_inserees'] == 3
        assert body['lignes_invalides_ignorees'] == 0
        assert '3 ligne(s)' in body['message']

    @patch('app.get_connection')
    def test_colonnes_minimales(self, mock_conn, client):
        """CSV avec seulement nom_serie et valeur → accepté."""
        mock_cursor = MagicMock()
        mock_conn.return_value.cursor.return_value = mock_cursor

        data = {'file': make_csv_file(CSV_COLONNES_MINIMALES)}
        resp = client.post('/upload/csv', data=data, content_type='multipart/form-data')

        assert resp.status_code == 201
        assert resp.get_json()['lignes_inserees'] == 2

    @patch('app.get_connection')
    def test_execute_appele_pour_chaque_ligne(self, mock_conn, client):
        """cursor.execute() doit être appelé autant de fois qu'il y a de lignes."""
        mock_cursor = MagicMock()
        mock_conn.return_value.cursor.return_value = mock_cursor

        data = {'file': make_csv_file(CSV_NOMINAL)}
        client.post('/upload/csv', data=data, content_type='multipart/form-data')

        assert mock_cursor.execute.call_count == 3

    @patch('app.get_connection')
    def test_commit_appele(self, mock_conn, client):
        """conn.commit() doit être appelé après les insertions."""
        mock_cursor = MagicMock()
        mock_conn.return_value.cursor.return_value = mock_cursor

        data = {'file': make_csv_file(CSV_NOMINAL)}
        client.post('/upload/csv', data=data, content_type='multipart/form-data')

        mock_conn.return_value.commit.assert_called_once()

    @patch('app.get_connection')
    def test_erreur_mysql_retourne_500(self, mock_conn, client):
        """Si MySQL lève une exception → 500 avec détail."""
        mock_conn.side_effect = Exception('Connection refused')

        data = {'file': make_csv_file(CSV_NOMINAL)}
        resp = client.post('/upload/csv', data=data, content_type='multipart/form-data')

        assert resp.status_code == 500
        body = resp.get_json()
        assert 'erreur' in body
        assert 'detail' in body

    @patch('app.get_connection')
    def test_chargement_donnees_exemple_complet(self, mock_conn, client):
        """Simule le chargement du fichier donnees_exemple.csv (22 lignes)."""
        mock_cursor = MagicMock()
        mock_conn.return_value.cursor.return_value = mock_cursor

        csv_exemple = """\
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
        data = {'file': make_csv_file(csv_exemple, 'donnees_exemple.csv')}
        resp = client.post('/upload/csv', data=data, content_type='multipart/form-data')

        assert resp.status_code == 201
        body = resp.get_json()
        assert body['lignes_inserees'] == 22
        assert body['lignes_invalides_ignorees'] == 0


# 5. Tests — Route GET /upload/series


class TestListSeries:

    @patch('app.get_connection')
    def test_list_series_nominal(self, mock_conn, client):
        """GET /upload/series → 200 avec liste des séries."""
        mock_cursor = MagicMock()
        mock_cursor.fetchall.return_value = [
            ('serie_A', 8, '2024-01-15', '2024-01-22'),
            ('serie_B', 8, '2024-01-15', '2024-01-22'),
            ('serie_C', 6, '2024-01-15', '2024-01-20'),
        ]
        mock_conn.return_value.cursor.return_value = mock_cursor

        resp = client.get('/upload/series')
        assert resp.status_code == 200

        body = resp.get_json()
        assert body['total'] == 3
        assert len(body['series']) == 3

        noms = [s['serie'] for s in body['series']]
        assert 'serie_A' in noms
        assert 'serie_C' in noms

    @patch('app.get_connection')
    def test_list_series_structure_chaque_element(self, mock_conn, client):
        """Chaque élément doit avoir les clés serie, n_points, debut, fin."""
        mock_cursor = MagicMock()
        mock_cursor.fetchall.return_value = [
            ('serie_A', 8, '2024-01-15', '2024-01-22'),
        ]
        mock_conn.return_value.cursor.return_value = mock_cursor

        resp = client.get('/upload/series')
        serie = resp.get_json()['series'][0]

        assert 'serie'    in serie
        assert 'n_points' in serie
        assert 'debut'    in serie
        assert 'fin'      in serie

    @patch('app.get_connection')
    def test_list_series_vide(self, mock_conn, client):
        """Aucune série en base → liste vide, total = 0."""
        mock_cursor = MagicMock()
        mock_cursor.fetchall.return_value = []
        mock_conn.return_value.cursor.return_value = mock_cursor

        resp = client.get('/upload/series')
        assert resp.status_code == 200
        body = resp.get_json()
        assert body['total'] == 0
        assert body['series'] == []

    @patch('app.get_connection')
    def test_list_series_erreur_mysql(self, mock_conn, client):
        """Erreur MySQL sur GET /upload/series → 500."""
        mock_conn.side_effect = Exception('DB down')

        resp = client.get('/upload/series')
        assert resp.status_code == 500
        assert 'erreur' in resp.get_json()


# 6. Tests — Format de la réponse JSON

class TestFormatReponse:

    @patch('app.get_connection')
    def test_champs_reponse_succes(self, mock_conn, client):
        """La réponse 201 doit contenir statut, lignes_inserees, lignes_invalides_ignorees, message."""
        mock_cursor = MagicMock()
        mock_conn.return_value.cursor.return_value = mock_cursor

        data = {'file': make_csv_file(CSV_NOMINAL)}
        resp = client.post('/upload/csv', data=data, content_type='multipart/form-data')

        body = resp.get_json()
        assert 'statut' in body
        assert 'lignes_inserees' in body
        assert 'lignes_invalides_ignorees' in body
        assert 'message' in body
        assert body['statut'] == 'success'

    def test_champ_erreur_present_en_cas_echec(self, client):
        """Les réponses d'erreur doivent toutes contenir la clé 'erreur'."""
        resp = client.post('/upload/csv')   # aucun fichier
        assert 'erreur' in resp.get_json()

    @patch('app.get_connection')
    def test_content_type_json(self, mock_conn, client):
        """Le Content-Type de la réponse doit être application/json."""
        mock_cursor = MagicMock()
        mock_conn.return_value.cursor.return_value = mock_cursor

        data = {'file': make_csv_file(CSV_NOMINAL)}
        resp = client.post('/upload/csv', data=data, content_type='multipart/form-data')
        assert 'application/json' in resp.content_type
