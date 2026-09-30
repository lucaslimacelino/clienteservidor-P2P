"""P2P simplificado, inspirado no modelo de distribuicao por chunks.

Um seed possui todos os chunks.
Cada peer baixa de vizinhos e, assim que possui um chunk, passa a servi-lo.
"""
import random
import socket
import struct
import threading
import time

from common import CHUNK, RateLimiter, recv_exact, recv_exact_discard


class Peer:
    def __init__(self, pid, port, size, rate_bps, is_seed, neighbors):
        self.pid = pid
        self.port = port
        self.size = size
        self.nchunks = (size + CHUNK - 1) // CHUNK
        self.is_seed = is_seed
        self.neighbors = neighbors

        self.have = bytearray(b"\x01" * self.nchunks) if is_seed else bytearray(self.nchunks)
        self.count = self.nchunks if is_seed else 0
        self.inflight = set()
        self.lock = threading.Lock()
        self.limiter = RateLimiter(rate_bps)

        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.sock.bind(("127.0.0.1", port))
        self.sock.listen(128)

        threading.Thread(target=self._accept, daemon=True).start()

    def _accept(self):
        while True:
            try:
                conn, _ = self.sock.accept()
                threading.Thread(
                    target=self._serve, args=(conn,), daemon=True
                ).start()
            except OSError:
                break

    def _chunk_size(self, idx):
        start = idx * CHUNK
        return min(CHUNK, self.size - start)

    def _serve(self, conn):
        try:
            with conn:
                conn.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)

                while True:
                    op = recv_exact(conn, 1)

                    if op == b"B":
                        with self.lock:
                            bits = bytes(self.have)
                        conn.sendall(bits)

                    elif op == b"G":
                        idx = struct.unpack(">I", recv_exact(conn, 4))[0]

                        with self.lock:
                            available = bool(self.have[idx])

                        if not available:
                            conn.sendall(b"\x00")
                            continue

                        start = idx * CHUNK
                        n = self._chunk_size(idx)

                        with self.lock:
                            block = bytes(self._payload(start, n))

                        self.limiter.consume(n)
                        conn.sendall(b"\x01" + block)
                    else:
                        return
        except (ConnectionError, OSError, IndexError):
            pass

    def _payload(self, start, n):
        # Para o experimento, o seed gera bytes determinísticos em memoria.
        # O conteúdo nao precisa ser salvo pelo cliente.
        return b"\x5a" * n

    def _pick(self, remote):
        with self.lock:
            candidates = [
                i for i in range(self.nchunks)
                if remote[i] and not self.have[i] and i not in self.inflight
            ]

            if not candidates:
                return None

            i = random.choice(candidates)
            self.inflight.add(i)
            return i

    def _downloader(self, neighbor_port):
        buf = bytearray(CHUNK)

        try:
            with socket.create_connection(("127.0.0.1", neighbor_port), timeout=10) as s:
                s.settimeout(30)
                s.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)

                remote = bytearray(self.nchunks)
                requests_since_bitfield = 999

                while True:
                    with self.lock:
                        if self.count >= self.nchunks:
                            break

                    if requests_since_bitfield >= 16:
                        s.sendall(b"B")
                        remote = bytearray(recv_exact(s, self.nchunks))
                        requests_since_bitfield = 0

                    idx = self._pick(remote)

                    if idx is None:
                        time.sleep(0.01)
                        requests_since_bitfield = 16
                        continue

                    try:
                        s.sendall(b"G" + struct.pack(">I", idx))
                        ok = recv_exact(s, 1)

                        if ok == b"\x01":
                            n = self._chunk_size(idx)
                            recv_exact_discard(s, n, buf)

                            with self.lock:
                                if not self.have[idx]:
                                    self.have[idx] = 1
                                    self.count += 1
                                self.inflight.discard(idx)
                        else:
                            remote[idx] = 0
                            with self.lock:
                                self.inflight.discard(idx)
                    except Exception:
                        with self.lock:
                            self.inflight.discard(idx)
                        break

                    requests_since_bitfield += 1
        except Exception:
            return

    def download(self):
        threads = [
            threading.Thread(target=self._downloader, args=(p,), daemon=True)
            for p in self.neighbors
        ]

        for t in threads:
            t.start()
        for t in threads:
            t.join()

    def close(self):
        try:
            self.sock.close()
        except OSError:
            pass


def peer_main(pid, base_port, size, rate_bps, is_seed, neighbors,
              barrier, done_evt, out_q):
    peer = Peer(
        pid=pid,
        port=base_port + pid,
        size=size,
        rate_bps=rate_bps,
        is_seed=is_seed,
        neighbors=[base_port + x for x in neighbors],
    )

    barrier.wait()

    if not is_seed:
        t0 = time.perf_counter()
        peer.download()
        elapsed = time.perf_counter() - t0
        out_q.put((pid, elapsed))

    done_evt.wait()
    peer.close()
