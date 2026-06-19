# benchmark.py — Compare Python pur vs C/ctypes

import time
import random
import c_bridge as C

# Générer un grand tableau de 1 000 000 valeurs aléatoires
N = 1_000_000
data = [random.gauss(50, 10) for _ in range(N)]

# ─── Python pur ────────────────────────────────────────────────
start = time.perf_counter()
mean_py = sum(data) / len(data)
elapsed_py = time.perf_counter() - start

print(
    f"Python pur  : moyenne = {mean_py:.4f} "
    f"[{elapsed_py * 1000:.2f} ms]"
)

# ─── C via ctypes ──────────────────────────────────────────────
start = time.perf_counter()
mean_c = C.moyenne(data)
elapsed_c = time.perf_counter() - start

print(
    f"C / ctypes  : moyenne = {mean_c:.4f} "
    f"[{elapsed_c * 1000:.2f} ms]"
)

if elapsed_c > 0:
    print(f"Gain de vitesse : x{elapsed_py / elapsed_c:.1f}")