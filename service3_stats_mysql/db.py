import os
import mysql.connector
from dotenv import load_dotenv

# Charge les variables du fichier .env
load_dotenv()


def get_connection():
    """
    Crée et retourne une connexion à la base MySQL.
    """
    return mysql.connector.connect(
        host=os.getenv("DB_HOST", "127.0.0.1"),
        port=int(os.getenv("DB_PORT", "3306")),
        user=os.getenv("DB_USER", "root"),
        password=os.getenv("DB_PASSWORD", ""),
        database=os.getenv("DB_NAME", "flask_stats")
    )


def fetch_series(nom_serie):
    """
    Récupère toutes les valeurs d'une série depuis la table donnees.
    Exemple : fetch_series("serie_A")
    """
    conn = get_connection()
    cursor = conn.cursor()

    try:
        cursor.execute(
            """
            SELECT valeur
            FROM donnees
            WHERE nom_serie = %s
            ORDER BY date_mesure
            """,
            (nom_serie,)
        )

        rows = cursor.fetchall()

        if not rows:
            raise ValueError(f"Aucune donnée trouvée pour la série '{nom_serie}'")

        return [float(row[0]) for row in rows]

    finally:
        cursor.close()
        conn.close()