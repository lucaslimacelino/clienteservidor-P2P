"""Executa a bateria completa de experimentos.

Padrao:
- tamanhos: 5, 50, 500 MB
- clientes: 1, 2, 4, 8
- arquiteturas: seq, thread, pool, p2p
- repeticoes: 3 para 5/50 MB e 1 para 500 MB
"""
import json
import os
import subprocess
import sys

SIZES = [5, 50, 500]
CLIENTS = [1, 2, 4, 8]
ARCHS = ["seq", "thread", "pool", "p2p"]

RATE_MB = 100
POOL = 4
OUT = "results.jsonl"


def already_done(arch, size, n, rep):
    if not os.path.exists(OUT):
        return False

    with open(OUT, encoding="utf-8") as f:
        for line in f:
            if not line.strip():
                continue
            r = json.loads(line)
            if (
                r["arch"] == arch
                and r["size_mb"] == size
                and r["n"] == n
                and r["rep"] == rep
            ):
                return True

    return False


def main():
    # Garante que os arquivos existem.
    subprocess.run([sys.executable, "make_files.py"], check=True)

    for size in SIZES:
        reps = 1 if size == 500 else 3

        for n in CLIENTS:
            for rep in range(1, reps + 1):
                for arch in ARCHS:
                    if already_done(arch, size, n, rep):
                        print(
                            f"SKIP {arch} {size}MB N={n} rep={rep}"
                        )
                        continue

                    cmd = [
                        sys.executable,
                        "run_exp.py",
                        "--arch", arch,
                        "--size_mb", str(size),
                        "--n", str(n),
                        "--rate_mb", str(RATE_MB),
                        "--pool", str(POOL),
                        "--rep", str(rep),
                        "--out", OUT,
                    ]

                    subprocess.run(cmd, check=True)

    print("\nBATERIA CONCLUIDA.")
    print("Agora execute: python make_report.py")


if __name__ == "__main__":
    main()
