import csv
import json
import statistics
from pathlib import Path
import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parent
RESULTS = ROOT / "resultados" / "results.jsonl"
OUT_CSV = ROOT / "resultados" / "estatisticas.csv"
GRAPH_DIR = ROOT / "resultados" / "graficos"


def main():
    if not RESULTS.exists():
        raise FileNotFoundError("Execute primeiro run_exp.py ou run_all.py.")

    data = []
    with open(RESULTS, encoding="utf-8") as f:
        for line in f:
            if line.strip():
                data.append(json.loads(line))

    groups = {}
    for r in data:
        groups.setdefault((r["arch"], r["size_mb"], r["n"]), []).append(r)

    rows = []
    for (arch, size, n), reps in sorted(groups.items()):
        avgs = [r["tavg"] for r in reps]
        rows.append({
            "arquitetura": arch,
            "tamanho_mb": size,
            "clientes": n,
            "repeticoes": len(reps),
            "minimo_s": statistics.mean(r["tmin"] for r in reps),
            "medio_s": statistics.mean(avgs),
            "maximo_s": statistics.mean(r["tmax"] for r in reps),
            "desvio_padrao_s": statistics.stdev(avgs) if len(avgs) > 1 else 0.0,
        })

    OUT_CSV.parent.mkdir(parents=True, exist_ok=True)
    with open(OUT_CSV, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=[
            "arquitetura", "tamanho_mb", "clientes", "repeticoes",
            "minimo_s", "medio_s", "maximo_s", "desvio_padrao_s"
        ])
        writer.writeheader()
        writer.writerows(rows)

    GRAPH_DIR.mkdir(parents=True, exist_ok=True)

    for size in sorted({r["tamanho_mb"] for r in rows}):
        subset = [r for r in rows if r["tamanho_mb"] == size]
        plt.figure(figsize=(10, 6))
        for arch in sorted({r["arquitetura"] for r in subset}):
            vals = sorted(
                [r for r in subset if r["arquitetura"] == arch],
                key=lambda x: x["clientes"]
            )
            plt.plot([r["clientes"] for r in vals], [r["medio_s"] for r in vals], marker="o", label=arch)
        plt.xlabel("Numero de clientes")
        plt.ylabel("Tempo medio (s)")
        plt.title(f"Tempo medio - {size} MB")
        plt.legend()
        plt.grid(True, alpha=0.3)
        plt.tight_layout()
        plt.savefig(GRAPH_DIR / f"{size}MB.png", dpi=150)
        plt.close()

    plt.figure(figsize=(10, 6))
    for arch in sorted({r["arquitetura"] for r in rows}):
        vals = []
        for size in sorted({r["tamanho_mb"] for r in rows}):
            subset = [r for r in rows if r["arquitetura"] == arch and r["tamanho_mb"] == size]
            if subset:
                vals.append((size, max(subset, key=lambda x: x["clientes"])["medio_s"]))
        if vals:
            plt.plot([x for x, _ in vals], [y for _, y in vals], marker="o", label=arch)
    plt.xlabel("Tamanho do arquivo (MB)")
    plt.ylabel("Tempo medio (s)")
    plt.title("Tempo medio por arquitetura")
    plt.legend()
    plt.grid(True, alpha=0.3)
    plt.tight_layout()
    plt.savefig(GRAPH_DIR / "comparacao.png", dpi=150)
    plt.close()

    print(f"Gerado: {OUT_CSV}")
    print(f"Graficos: {GRAPH_DIR}")


if __name__ == "__main__":
    main()
