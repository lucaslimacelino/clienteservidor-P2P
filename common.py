"""Utilitarios comuns para os experimentos."""
import socket
import struct
import threading
import time

CHUNK = 256 * 1024
BUFFER = 256 * 1024


class RateLimiter:
    """Limita a taxa agregada de upload de um no (bytes/s)."""
    def __init__(self, rate_bps):
        self.rate = float(rate_bps)
        self.next_free = time.perf_counter()
        self.lock = threading.Lock()

    def consume(self, n):
        if self.rate <= 0:
            return
        with self.lock:
            now = time.perf_counter()
            start = max(self.next_free, now)
            self.next_free = start + n / self.rate
        wait = start - now
        if wait > 0:
            time.sleep(wait)


def recv_exact(sock, n):
    data = bytearray()
    while len(data) < n:
        chunk = sock.recv(n - len(data))
        if not chunk:
            raise ConnectionError("conexao fechada")
        data += chunk
    return bytes(data)


def recv_exact_discard(sock, n, buf):
    """Recebe n bytes e descarta; nao grava o arquivo em disco."""
    mv = memoryview(buf)
    got = 0
    while got < n:
        r = sock.recv_into(mv, min(len(buf), n - got))
        if r == 0:
            raise ConnectionError("conexao fechada")
        got += r
    return got
