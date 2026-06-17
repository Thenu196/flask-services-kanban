#!/bin/bash
# ============================================================
#  Tests Service 4 — Chargement CSV vers MySQL
# ============================================================

BASE_URL="http://localhost:5004"

echo "========================================"
echo "TEST 1 — Chargement nominal (donnees_exemple.csv)"
echo "========================================"
curl -s -X POST "$BASE_URL/upload/csv" \
     -F 'file=@data/donnees_exemple.csv' | python3 -m json.tool

echo ""
echo "========================================"
echo "TEST 2 — Lister les séries disponibles"
echo "========================================"
curl -s "$BASE_URL/upload/series" | python3 -m json.tool

echo ""
echo "========================================"
echo "TEST 3 — Fichier sans colonne 'valeur' (erreur attendue 400)"
echo "========================================"
echo "nom_serie,categorie
serie_X,temperature" > /tmp/sans_valeur.csv
curl -s -X POST "$BASE_URL/upload/csv" \
     -F 'file=@/tmp/sans_valeur.csv' | python3 -m json.tool

echo ""
echo "========================================"
echo "TEST 4 — CSV avec valeurs non numériques dans 'valeur'"
echo "========================================"
echo "nom_serie,valeur,categorie,date_mesure
serie_X,abc,temperature,2024-01-15
serie_X,12.5,temperature,2024-01-16
serie_X,,temperature,2024-01-17" > /tmp/valeurs_invalides.csv
curl -s -X POST "$BASE_URL/upload/csv" \
     -F 'file=@/tmp/valeurs_invalides.csv' | python3 -m json.tool

echo ""
echo "========================================"
echo "TEST 5 — Aucun fichier envoyé (erreur attendue 400)"
echo "========================================"
curl -s -X POST "$BASE_URL/upload/csv" | python3 -m json.tool

echo ""
echo "========================================"
echo "TEST 6 — Fichier non-CSV (erreur attendue 400)"
echo "========================================"
echo "ceci n'est pas un csv" > /tmp/fichier.txt
curl -s -X POST "$BASE_URL/upload/csv" \
     -F 'file=@/tmp/fichier.txt' | python3 -m json.tool
