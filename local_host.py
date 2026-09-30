#!/usr/bin/env python3
"""Vynx.dev local WebKit + User Guide host.

Runs:
  - DNS redirect on port 53 for the PlayStation User Guide -> this PC
  - DNS blocking for PlayStation/Sony online + update domains
  - HTTP static server on port 80
  - HTTPS static server on port 443 (self-signed cert generated on first run)

Non-PlayStation DNS requests are forwarded to an upstream resolver.
"""

from __future__ import annotations

import argparse
import base64
import hashlib
import http.server
import ipaddress
import os
import secrets
import socket
import socketserver
import ssl
import struct
import sys
import threading
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path
from urllib.parse import urlsplit

ROOT = Path(__file__).resolve().parent
STATE_DIR = ROOT / ".local-host"
CERT_PATH = STATE_DIR / "cert.pem"
KEY_PATH = STATE_DIR / "key.pem"
GUIDE_HOSTS = {"manuals.playstation.net", "manuals.playstation.com"}

# Keep the console away from PSN/update infrastructure while this DNS is in use.
# User Guide hosts above are handled first, so they still resolve to this PC.
PSN_BLOCK_SUFFIXES = (
    "playstation.net",
    "playstation.com",
    "playstation.org",
    "sonyentertainmentnetwork.com",
    "scea.com",
    "sie-rd.com",
)
DEFAULT_UPSTREAM = "1.1.1.1"


# ----------------------------- Networking helpers -----------------------------

def detect_lan_ip() -> str:
    """Best-effort detection of the IPv4 address used for the default route."""
    candidates: list[str] = []

    for target in (("1.1.1.1", 53), ("8.8.8.8", 53)):
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        try:
            sock.connect(target)
            candidates.append(sock.getsockname()[0])
        except OSError:
            pass
        finally:
            sock.close()

    try:
        candidates.append(socket.gethostbyname(socket.gethostname()))
    except OSError:
        pass

    for candidate in candidates:
        try:
            addr = ipaddress.ip_address(candidate)
        except ValueError:
            continue
        if addr.version == 4 and not addr.is_loopback and not addr.is_link_local:
            return candidate

    raise RuntimeError(
        "Could not detect a usable LAN IPv4 address. "
        "Run: py -3 local_host.py --ip YOUR_PC_IP"
    )


def parse_dns_question(packet: bytes) -> tuple[str, int, int, int]:
    """Return (qname, qtype, qclass, end_of_question)."""
    if len(packet) < 12:
        raise ValueError("DNS packet too short")

    offset = 12
    labels: list[str] = []

    while True:
        if offset >= len(packet):
            raise ValueError("Malformed DNS name")
        length = packet[offset]
        offset += 1
        if length == 0:
            break
        if length & 0xC0:
            raise ValueError("Compressed DNS question names are not supported")
        if offset + length > len(packet):
            raise ValueError("Malformed DNS label")
        labels.append(packet[offset:offset + length].decode("ascii", "ignore"))
        offset += length

    if offset + 4 > len(packet):
        raise ValueError("DNS question missing type/class")

    qtype, qclass = struct.unpack("!HH", packet[offset:offset + 4])
    return ".".join(labels).lower(), qtype, qclass, offset + 4


def is_psn_blocked(qname: str) -> bool:
    qname = qname.rstrip(".").lower()
    if qname in GUIDE_HOSTS:
        return False
    return any(qname == suffix or qname.endswith("." + suffix) for suffix in PSN_BLOCK_SUFFIXES)


def build_block_response(query: bytes) -> bytes:
    """Return a successful DNS response that points A queries at 0.0.0.0."""
    _qname, qtype, qclass, qend = parse_dns_question(query)
    transaction_id = query[:2]
    request_flags = struct.unpack("!H", query[2:4])[0]
    rd = request_flags & 0x0100
    flags = 0x8400 | rd | 0x0080
    answer_count = 1 if qclass == 1 and qtype in (1, 255) else 0
    header = transaction_id + struct.pack("!HHHHH", flags, 1, answer_count, 0, 0)
    question = query[12:qend]

    if answer_count == 0:
        return header + question

    answer = (
        b"\xc0\x0c"
        + struct.pack("!HHI", 1, 1, 60)
        + struct.pack("!H", 4)
        + socket.inet_aton("0.0.0.0")
    )
    return header + question + answer


def build_a_response(query: bytes, ip: str) -> bytes:
    qname, qtype, qclass, qend = parse_dns_question(query)
    transaction_id = query[:2]
    request_flags = struct.unpack("!H", query[2:4])[0]
    rd = request_flags & 0x0100

    # QR=1, AA=1, RD copied, RA=1, RCODE=0
    flags = 0x8400 | rd | 0x0080
    answer_count = 1 if qclass == 1 and qtype in (1, 255) else 0
    header = transaction_id + struct.pack("!HHHHH", flags, 1, answer_count, 0, 0)
    question = query[12:qend]

    if answer_count == 0:
        return header + question

    answer = (
        b"\xc0\x0c"                    # compressed name pointer to QNAME
        + struct.pack("!HHI", 1, 1, 60)  # A, IN, TTL 60
        + struct.pack("!H", 4)
        + socket.inet_aton(ip)
    )
    return header + question + answer


def forward_dns_udp(packet: bytes, upstream: str, timeout: float = 3.0) -> bytes:
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.settimeout(timeout)
    try:
        sock.sendto(packet, (upstream, 53))
        response, _ = sock.recvfrom(65535)
        return response
    finally:
        sock.close()


def forward_dns_tcp(packet: bytes, upstream: str, timeout: float = 3.0) -> bytes:
    with socket.create_connection((upstream, 53), timeout=timeout) as sock:
        sock.sendall(struct.pack("!H", len(packet)) + packet)
        header = _recv_exact(sock, 2)
        length = struct.unpack("!H", header)[0]
        return _recv_exact(sock, length)


def _recv_exact(sock: socket.socket, count: int) -> bytes:
    chunks: list[bytes] = []
    remaining = count
    while remaining:
        chunk = sock.recv(remaining)
        if not chunk:
            raise ConnectionError("Socket closed while receiving DNS response")
        chunks.append(chunk)
        remaining -= len(chunk)
    return b"".join(chunks)


class ReusableThreadingUDPServer(socketserver.ThreadingUDPServer):
    allow_reuse_address = True
    daemon_threads = True


class ReusableThreadingTCPServer(socketserver.ThreadingTCPServer):
    allow_reuse_address = True
    daemon_threads = True


class DNSUDPHandler(socketserver.BaseRequestHandler):
    def handle(self) -> None:
        packet, sock = self.request
        server: "DNSUDPServer" = self.server  # type: ignore[assignment]
        try:
            qname, _, _, _ = parse_dns_question(packet)
            if qname in GUIDE_HOSTS:
                response = build_a_response(packet, server.redirect_ip)
                if server.verbose:
                    print(f"[DNS] GUIDE  {qname} -> {server.redirect_ip}")
            elif server.block_psn and is_psn_blocked(qname):
                response = build_block_response(packet)
                if server.verbose:
                    print(f"[DNS] BLOCK  {qname}")
            else:
                response = forward_dns_udp(packet, server.upstream)
                if server.verbose:
                    print(f"[DNS] PASS   {qname}")
            sock.sendto(response, self.client_address)
        except Exception as exc:
            if server.verbose:
                print(f"[DNS] UDP request failed: {exc}")


class DNSTCPHandler(socketserver.BaseRequestHandler):
    def handle(self) -> None:
        server: "DNSTCPServer" = self.server  # type: ignore[assignment]
        try:
            raw_len = _recv_exact(self.request, 2)
            msg_len = struct.unpack("!H", raw_len)[0]
            packet = _recv_exact(self.request, msg_len)
            qname, _, _, _ = parse_dns_question(packet)
            if qname in GUIDE_HOSTS:
                response = build_a_response(packet, server.redirect_ip)
                if server.verbose:
                    print(f"[DNS] GUIDE  {qname} -> {server.redirect_ip} (TCP)")
            elif server.block_psn and is_psn_blocked(qname):
                response = build_block_response(packet)
                if server.verbose:
                    print(f"[DNS] BLOCK  {qname} (TCP)")
            else:
                response = forward_dns_tcp(packet, server.upstream)
                if server.verbose:
                    print(f"[DNS] PASS   {qname} (TCP)")
            self.request.sendall(struct.pack("!H", len(response)) + response)
        except Exception as exc:
            if server.verbose:
                print(f"[DNS] TCP request failed: {exc}")


class DNSUDPServer(ReusableThreadingUDPServer):
    def __init__(self, address: tuple[str, int], redirect_ip: str, upstream: str, block_psn: bool, verbose: bool):
        self.redirect_ip = redirect_ip
        self.upstream = upstream
        self.block_psn = block_psn
        self.verbose = verbose
        super().__init__(address, DNSUDPHandler)


class DNSTCPServer(ReusableThreadingTCPServer):
    def __init__(self, address: tuple[str, int], redirect_ip: str, upstream: str, block_psn: bool, verbose: bool):
        self.redirect_ip = redirect_ip
        self.upstream = upstream
        self.block_psn = block_psn
        self.verbose = verbose
        super().__init__(address, DNSTCPHandler)


# ----------------------------- Static web hosting -----------------------------

class VynxRequestHandler(http.server.SimpleHTTPRequestHandler):
    """Serve the project root and bounce Sony User Guide paths to /."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(ROOT), **kwargs)

    def _maybe_redirect_user_guide(self) -> bool:
        path = urlsplit(self.path).path
        if path.startswith("/document/") or path in {"/document", "/document/"}:
            self.send_response(302)
            self.send_header("Location", "/")
            self.send_header("Cache-Control", "no-store")
            self.end_headers()
            return True
        return False

    def do_GET(self) -> None:  # noqa: N802
        if self._maybe_redirect_user_guide():
            return
        super().do_GET()

    def do_HEAD(self) -> None:  # noqa: N802
        if self._maybe_redirect_user_guide():
            return
        super().do_HEAD()

    def end_headers(self) -> None:
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("X-Vynx-Local-Host", "1")
        super().end_headers()

    def log_message(self, fmt: str, *args) -> None:
        if getattr(self.server, "verbose", False):
            print(f"[WEB] {self.address_string()} - {fmt % args}")


class ReusableThreadingHTTPServer(http.server.ThreadingHTTPServer):
    allow_reuse_address = True
    daemon_threads = True


# ------------------------- Self-signed cert generation ------------------------
# Pure-Python RSA/X.509 generation avoids requiring OpenSSL or pip packages.

def _der_len(length: int) -> bytes:
    if length < 0x80:
        return bytes([length])
    raw = length.to_bytes((length.bit_length() + 7) // 8, "big")
    return bytes([0x80 | len(raw)]) + raw


def _der(tag: int, payload: bytes) -> bytes:
    return bytes([tag]) + _der_len(len(payload)) + payload


def _seq(*parts: bytes) -> bytes:
    return _der(0x30, b"".join(parts))


def _set(*parts: bytes) -> bytes:
    return _der(0x31, b"".join(parts))


def _integer(value: int) -> bytes:
    if value == 0:
        raw = b"\x00"
    else:
        raw = value.to_bytes((value.bit_length() + 7) // 8, "big")
        if raw[0] & 0x80:
            raw = b"\x00" + raw
    return _der(0x02, raw)


def _null() -> bytes:
    return b"\x05\x00"


def _oid(text: str) -> bytes:
    nums = [int(x) for x in text.split(".")]
    if len(nums) < 2:
        raise ValueError("Invalid OID")
    encoded = bytearray([40 * nums[0] + nums[1]])
    for n in nums[2:]:
        stack = [n & 0x7F]
        n >>= 7
        while n:
            stack.append(0x80 | (n & 0x7F))
            n >>= 7
        encoded.extend(reversed(stack))
    return _der(0x06, bytes(encoded))


def _utf8(text: str) -> bytes:
    return _der(0x0C, text.encode("utf-8"))


def _octet(data: bytes) -> bytes:
    return _der(0x04, data)


def _bitstring(data: bytes) -> bytes:
    return _der(0x03, b"\x00" + data)


def _utc_time(dt: datetime) -> bytes:
    return _der(0x17, dt.strftime("%y%m%d%H%M%SZ").encode("ascii"))


def _ctx_explicit(tag_num: int, content: bytes) -> bytes:
    return _der(0xA0 + tag_num, content)


def _pem(label: str, der: bytes) -> bytes:
    body = base64.encodebytes(der).replace(b"\n", b"")
    lines = [body[i:i + 64] for i in range(0, len(body), 64)]
    return (
        f"-----BEGIN {label}-----\n".encode()
        + b"\n".join(lines)
        + f"\n-----END {label}-----\n".encode()
    )


def _is_probable_prime(n: int, rounds: int = 40) -> bool:
    if n < 2:
        return False
    small_primes = (2, 3, 5, 7, 11, 13, 17, 19, 23, 29, 31, 37, 41, 43, 47)
    for p in small_primes:
        if n == p:
            return True
        if n % p == 0:
            return False

    d = n - 1
    s = 0
    while d % 2 == 0:
        s += 1
        d //= 2

    for _ in range(rounds):
        a = secrets.randbelow(n - 3) + 2
        x = pow(a, d, n)
        if x in (1, n - 1):
            continue
        for _ in range(s - 1):
            x = pow(x, 2, n)
            if x == n - 1:
                break
        else:
            return False
    return True


def _generate_prime(bits: int, e: int) -> int:
    while True:
        n = secrets.randbits(bits) | (1 << (bits - 1)) | 1
        if (n - 1) % e == 0:
            continue
        if _is_probable_prime(n):
            return n


def generate_certificate(cert_path: Path, key_path: Path) -> None:
    e = 65537
    p = _generate_prime(1024, e)
    q = _generate_prime(1024, e)
    while q == p:
        q = _generate_prime(1024, e)
    if p < q:
        p, q = q, p

    n = p * q
    phi = (p - 1) * (q - 1)
    d = pow(e, -1, phi)
    dmp1 = d % (p - 1)
    dmq1 = d % (q - 1)
    iqmp = pow(q, -1, p)

    private_key = _seq(
        _integer(0), _integer(n), _integer(e), _integer(d),
        _integer(p), _integer(q), _integer(dmp1), _integer(dmq1), _integer(iqmp)
    )

    rsa_alg = _seq(_oid("1.2.840.113549.1.1.1"), _null())
    sig_alg = _seq(_oid("1.2.840.113549.1.1.11"), _null())
    public_key = _seq(_integer(n), _integer(e))
    spki = _seq(rsa_alg, _bitstring(public_key))

    common_name = _seq(_set(_seq(_oid("2.5.4.3"), _utf8("manuals.playstation.net"))))
    now = datetime.now(timezone.utc) - timedelta(days=1)
    expiry = now + timedelta(days=3650)
    validity = _seq(_utc_time(now), _utc_time(expiry))

    san_names = _seq(
        _der(0x82, b"manuals.playstation.net"),
        _der(0x82, b"manuals.playstation.com"),
    )
    san_extension = _seq(_oid("2.5.29.17"), _octet(san_names))
    extensions = _ctx_explicit(3, _seq(san_extension))

    serial = secrets.randbits(120) | 1
    tbs = _seq(
        _ctx_explicit(0, _integer(2)),
        _integer(serial),
        sig_alg,
        common_name,
        validity,
        common_name,
        spki,
        extensions,
    )

    digest_info = bytes.fromhex("3031300d060960864801650304020105000420") + hashlib.sha256(tbs).digest()
    key_bytes = (n.bit_length() + 7) // 8
    padding_len = key_bytes - len(digest_info) - 3
    if padding_len < 8:
        raise RuntimeError("RSA key too small for SHA-256 signature")
    encoded_message = b"\x00\x01" + (b"\xff" * padding_len) + b"\x00" + digest_info
    signature = pow(int.from_bytes(encoded_message, "big"), d, n).to_bytes(key_bytes, "big")

    certificate = _seq(tbs, sig_alg, _bitstring(signature))

    cert_path.parent.mkdir(parents=True, exist_ok=True)
    cert_path.write_bytes(_pem("CERTIFICATE", certificate))
    key_path.write_bytes(_pem("RSA PRIVATE KEY", private_key))

    try:
        os.chmod(key_path, 0o600)
    except OSError:
        pass



def ensure_certificate() -> tuple[Path, Path]:
    if not CERT_PATH.exists() or not KEY_PATH.exists():
        generate_certificate(CERT_PATH, KEY_PATH)
    return CERT_PATH, KEY_PATH


# --------------------------------- Main app -----------------------------------

def start_server_thread(server, label: str) -> threading.Thread:
    thread = threading.Thread(target=server.serve_forever, name=label, daemon=True)
    thread.start()
    return thread


def make_http_server(bind_ip: str, port: int, verbose: bool = False) -> ReusableThreadingHTTPServer:
    server = ReusableThreadingHTTPServer((bind_ip, port), VynxRequestHandler)
    server.verbose = verbose
    return server


def make_https_server(bind_ip: str, port: int, verbose: bool = False) -> ReusableThreadingHTTPServer:
    cert_path, key_path = ensure_certificate()
    server = ReusableThreadingHTTPServer((bind_ip, port), VynxRequestHandler)
    server.verbose = verbose
    context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
    context.load_cert_chain(certfile=str(cert_path), keyfile=str(key_path))
    server.socket = context.wrap_socket(server.socket, server_side=True)
    return server


def port_error(service: str, bind_ip: str, port: int, exc: OSError) -> str:
    if getattr(exc, "winerror", None) == 10048 or getattr(exc, "errno", None) in (48, 98, 10048):
        return (
            f"{service} could not start because {bind_ip}:{port} is already in use.\n"
            "Close the program/service using that port and run .START-HOST.bat again."
        )
    if getattr(exc, "winerror", None) == 10013 or getattr(exc, "errno", None) in (13, 10013):
        return (
            f"{service} could not bind to {bind_ip}:{port} (permission denied).\n"
            "Try right-clicking .START-HOST.bat and choosing 'Run as administrator'."
        )
    return f"{service} could not start on {bind_ip}:{port}: {exc}"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Vynx.dev local WebKit + User Guide host")
    parser.add_argument("--ip", help="LAN IPv4 address to advertise in DNS (auto-detected by default)")
    parser.add_argument("--upstream", default=DEFAULT_UPSTREAM, help="Upstream DNS resolver (default: 1.1.1.1)")
    parser.add_argument("--dns-port", type=int, default=53, help=argparse.SUPPRESS)
    parser.add_argument("--http-port", type=int, default=80, help=argparse.SUPPRESS)
    parser.add_argument("--https-port", type=int, default=443, help=argparse.SUPPRESS)
    parser.add_argument("--no-https", action="store_true", help="Disable HTTPS server")
    parser.add_argument("--allow-psn", action="store_true", help="Do not block PlayStation/Sony domains")
    parser.add_argument("--verbose", action="store_true", help="Show DNS and web request logs")
    parser.add_argument("--print-ip", action="store_true", help="Print detected LAN IP and exit")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    try:
        lan_ip = args.ip or detect_lan_ip()
        ipaddress.IPv4Address(lan_ip)
        ipaddress.IPv4Address(args.upstream)
    except Exception as exc:
        print(f"ERROR: {exc}")
        return 1

    if args.print_ip:
        print(lan_ip)
        return 0

    servers = []

    try:
        dns_udp = DNSUDPServer((lan_ip, args.dns_port), lan_ip, args.upstream, not args.allow_psn, args.verbose)
        servers.append((dns_udp, "DNS/UDP"))
    except OSError as exc:
        print("\nERROR: " + port_error("DNS (UDP)", lan_ip, args.dns_port, exc))
        return 1

    try:
        dns_tcp = DNSTCPServer((lan_ip, args.dns_port), lan_ip, args.upstream, not args.allow_psn, args.verbose)
        servers.append((dns_tcp, "DNS/TCP"))
    except OSError as exc:
        dns_udp.server_close()
        print("\nERROR: " + port_error("DNS (TCP)", lan_ip, args.dns_port, exc))
        return 1

    try:
        httpd = make_http_server("0.0.0.0", args.http_port, args.verbose)
        servers.append((httpd, "HTTP"))
    except OSError as exc:
        for server, _ in servers:
            server.server_close()
        print("\nERROR: " + port_error("HTTP", "0.0.0.0", args.http_port, exc))
        return 1

    if not args.no_https:
        try:
            httpsd = make_https_server("0.0.0.0", args.https_port, args.verbose)
            servers.append((httpsd, "HTTPS"))
        except OSError as exc:
            for server, _ in servers:
                server.server_close()
            print("\nERROR: " + port_error("HTTPS", "0.0.0.0", args.https_port, exc))
            return 1
        except Exception as exc:
            for server, _ in servers:
                server.server_close()
            print(f"\nERROR: HTTPS certificate/server setup failed: {exc}")
            return 1

    for server, label in servers:
        start_server_thread(server, label)

    # Keep the normal launcher screen intentionally simple.
    if os.name == "nt" and not args.verbose:
        os.system("cls")

    print()
    print("============================================")
    print("         Vynx.dev Jailbreak - READY")
    print("============================================")
    print()
    print("Set your PS4 / PS5 DNS to:")
    print()
    print(f"             {lan_ip}")
    print()
    print("Then open:")
    print("Settings -> User's Guide")
    print()
    print("Keep this window open.")
    print("Press CTRL+C to stop.")
    print("============================================")
    print()

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nStopping local host...")
    finally:
        for server, _ in servers:
            try:
                server.shutdown()
            except Exception:
                pass
        for server, _ in servers:
            try:
                server.server_close()
            except Exception:
                pass

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
