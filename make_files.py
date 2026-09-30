"""Gera os arquivos reais usados nos experimentos."""
import os

SIZES = [5, 50, 500]
CHUNK = 1024 * 1024


def make_file(path, mb):
    total = mb * CHUNK
    block = b"\xA5" * CHUNK

    os.makedirs(os.path.dirname(path), exist_ok=True)

    with open(path, "wb") as f:
        remaining = total
        while remaining:
            n = min(CHUNK, remaining)
            f.write(block[:n])
            remaining -= n


if __name__ == "__main__":
    for mb in SIZES:
        path = os.path.join("arquivos", f"{mb}MB.bin")

        if os.path.exists(path) and os.path.getsize(path) == mb * CHUNK:
            print(f"{path}: ja existe")
            continue

        print(f"Gerando {path}...")
        make_file(path, mb)
        print(f"OK: {path}")

    print("Arquivos prontos.")
