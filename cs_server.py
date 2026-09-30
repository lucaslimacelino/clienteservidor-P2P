"""Servidor cliente-servidor: seq, thread ou pool.

O arquivo e lido uma vez para memoria antes de aceitar clientes.
Isso evita que o disco vire o principal gargalo durante a comparacao.
"""
import os
import socket
import struct
import threading
from concurrent.futures import ThreadPoolExecutor
from common import RateLimiter, recv_exact, BUFFER


def serve(mode, port, file_path, rate_bps, pool_n=4, ready_evt=None):
    if mode not in {"seq", "thread", "pool"}:
        raise ValueError("mode deve ser seq, thread ou pool")

    with open(file_path, "rb") as f:
        data = f.read()

    size = len(data)
    limiter = RateLimiter(rate_bps)

    def handle(conn):
        try:
            with conn:
                conn.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
                if recv_exact(conn, 3) != b"GET":
                    return

                conn.sendall(struct.pack(">Q", size))

                sent = 0
                while sent < size:
                    end = min(sent + BUFFER, size)
                    block = data[sent:end]
                    limiter.consume(len(block))
                    conn.sendall(block)
                    sent = end
        except (ConnectionError, OSError):
            pass

    srv = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    srv.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    srv.bind(("127.0.0.1", port))
    srv.listen(512)

    if ready_evt is not None:
        ready_evt.set()

    pool = ThreadPoolExecutor(max_workers=pool_n) if mode == "pool" else None

    try:
        while True:
            conn, _ = srv.accept()

            if mode == "seq":
                handle(conn)
            elif mode == "thread":
                threading.Thread(
                    target=handle, args=(conn,), daemon=True
                ).start()
            else:
                pool.submit(handle, conn)
    finally:
        if pool:
            pool.shutdown(wait=False, cancel_futures=True)
        srv.close()
