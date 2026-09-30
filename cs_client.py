"""Cliente TCP. Recebe o arquivo e descarta os bytes."""
import socket
import struct
import time
from common import recv_exact, recv_exact_discard, BUFFER


def client(port, barrier, out_q, idx):
    barrier.wait()

    t0 = time.perf_counter()

    with socket.create_connection(("127.0.0.1", port)) as s:
        s.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
        s.sendall(b"GET")

        size = struct.unpack(">Q", recv_exact(s, 8))[0]

        buf = bytearray(BUFFER)
        recv_exact_discard(s, size, buf)

    elapsed = time.perf_counter() - t0
    out_q.put((idx, elapsed))
