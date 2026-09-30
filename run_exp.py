"""Executa um experimento e grava uma linha em results.jsonl."""
import argparse
import json
import multiprocessing as mp
import os
import random
import time

import cs_client
import cs_server
import p2p


BASE_PORT = 22000


def run_cs(mode, file_path, n, rate, pool_n):
    port = BASE_PORT + random.randint(0, 2000)

    ready = mp.Event()
    server = mp.Process(
        target=cs_server.serve,
        args=(mode, port, file_path, rate, pool_n, ready),
        daemon=True,
    )
    server.start()
    ready.wait(timeout=10)

    barrier = mp.Barrier(n)
    q = mp.Queue()

    clients = [
        mp.Process(
            target=cs_client.client,
            args=(port, barrier, q, i),
        )
        for i in range(n)
    ]

    for c in clients:
        c.start()

    results = [q.get(timeout=3600) for _ in range(n)]

    for c in clients:
        c.join(timeout=10)

    server.terminate()
    server.join(timeout=5)

    return [t for _, t in sorted(results)]


def run_p2p(size, n, rate, k=5):
    base = BASE_PORT + random.randint(3000, 5000)

    # pid 0 = seed; pid 1..n = clientes
    barrier = mp.Barrier(n + 1)
    done = mp.Event()
    q = mp.Queue()

    processes = []

    for pid in range(n + 1):
        if pid == 0:
            neighbors = []
        else:
            others = [x for x in range(1, n + 1) if x != pid]
            random.shuffle(others)
            neighbors = [0] + others[:max(0, k - 1)]

        proc = mp.Process(
            target=p2p.peer_main,
            args=(
                pid, base, size, rate, pid == 0,
                neighbors, barrier, done, q
            ),
            daemon=True,
        )
        proc.start()
        processes.append(proc)

    results = [q.get(timeout=3600) for _ in range(n)]

    done.set()

    for proc in processes:
        proc.join(timeout=5)
        if proc.is_alive():
            proc.terminate()

    return [t for _, t in sorted(results)]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--arch", required=True, choices=["seq", "thread", "pool", "p2p"])
    parser.add_argument("--size_mb", type=int, required=True)
    parser.add_argument("--n", type=int, required=True)
    parser.add_argument("--rate_mb", type=float, default=100)
    parser.add_argument("--pool", type=int, default=4)
    parser.add_argument("--rep", type=int, default=1)
    parser.add_argument("--out", default="results.jsonl")

    args = parser.parse_args()

    file_path = os.path.join("arquivos", f"{args.size_mb}MB.bin")
    if not os.path.exists(file_path):
        raise FileNotFoundError(
            f"{file_path} nao existe. Execute make_files.py primeiro."
        )

    size = args.size_mb * 1024 * 1024
    rate = args.rate_mb * 1024 * 1024

    start_wall = time.perf_counter()

    if args.arch == "p2p":
        times = run_p2p(size, args.n, rate)
    else:
        times = run_cs(args.arch, file_path, args.n, rate, args.pool)

    rec = {
        "arch": args.arch,
        "size_mb": args.size_mb,
        "n": args.n,
        "rep": args.rep,
        "rate_mb": args.rate_mb,
        "pool": args.pool,
        "times": times,
        "tmin": min(times),
        "tavg": sum(times) / len(times),
        "tmax": max(times),
        "wall": time.perf_counter() - start_wall,
    }

    with open(args.out, "a", encoding="utf-8") as f:
        f.write(json.dumps(rec) + "\n")

    print(
        f"{args.arch:6s} {args.size_mb:4d} MB "
        f"N={args.n:2d} "
        f"min={rec['tmin']:.3f}s "
        f"media={rec['tavg']:.3f}s "
        f"max={rec['tmax']:.3f}s"
    )


if __name__ == "__main__":
    main()
