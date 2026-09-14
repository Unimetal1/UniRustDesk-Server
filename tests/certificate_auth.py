# Run after cargo build --release: python tests/certificate_auth.py LOCAL_IPV4
# Requires cryptography and PyNaCl.
import asyncio
import base64
import os
from pathlib import Path
import socket
import subprocess
import sys
import tempfile
import uuid
from datetime import datetime, timedelta, timezone
from cryptography import x509
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding, rsa
from cryptography.x509.oid import NameOID
from nacl.bindings import (
    crypto_box,
    crypto_box_keypair,
    crypto_secretbox,
    crypto_secretbox_open,
    crypto_sign_keypair,
    crypto_sign_open,
)

SERVER = Path(__file__).resolve().parents[1]
IP = sys.argv[1]
RSA_KEY = rsa.generate_private_key(public_exponent=65537, key_size=3072)
PREFIX = b"RustDesk technician v1\0"


SERVER_PUBLIC_KEY, SERVER_SECRET_KEY = crypto_sign_keypair()
LICENSE = base64.b64encode(SERVER_PUBLIC_KEY)


def certificate(expired=False):
    now = datetime.now(timezone.utc)
    name = x509.Name([x509.NameAttribute(NameOID.COMMON_NAME, "technician")])
    return (x509.CertificateBuilder().subject_name(name).issuer_name(name)
            .public_key(RSA_KEY.public_key()).serial_number(x509.random_serial_number())
            .not_valid_before(now - timedelta(days=2))
            .not_valid_after(now + timedelta(days=-1 if expired else 1))
            .sign(RSA_KEY, hashes.SHA256()))


def varint(number):
    result = bytearray()
    while number > 127:
        result.append((number & 127) | 128)
        number >>= 7
    return bytes(result) + bytes([number])


def field(tag, value):
    if isinstance(value, str):
        value = value.encode()
    return varint(tag << 3 | 2) + varint(len(value)) + value


def parse_fields(data):
    fields = []
    offset = 0
    while offset < len(data):
        tag, offset = read_varint(data, offset)
        length, offset = read_varint(data, offset)
        fields.append((tag >> 3, data[offset:offset + length]))
        offset += length
    return fields


def read_varint(data, offset):
    value = 0
    shift = 0
    while True:
        byte = data[offset]
        offset += 1
        value |= (byte & 127) << shift
        if byte < 128:
            return value, offset
        shift += 7


def relay_request(session, technician):
    peer = field(1, "receiver-test") if technician else b""
    return field(18, peer + field(2, session) + field(6, LICENSE))


def frame(data):
    size = next(n for n in range(1, 5) if len(data) < 1 << (8 * n - 2))
    return ((len(data) << 2) | (size - 1)).to_bytes(size, "little") + data


async def receive_frame(reader):
    head = await reader.readexactly(1)
    head += await reader.readexactly(head[0] & 3)
    length = int.from_bytes(head, "little") >> 2
    return await asyncio.wait_for(reader.readexactly(length), 5)


class SecureConnection:
    def __init__(self, reader, writer, key):
        self.reader = reader
        self.writer = writer
        self.key = key
        self.send_sequence = 0
        self.receive_sequence = 0

    @staticmethod
    def nonce(sequence):
        return sequence.to_bytes(8, "little") + bytes(16)

    async def send(self, data):
        self.send_sequence += 1
        encrypted = crypto_secretbox(data, self.nonce(self.send_sequence), self.key)
        self.writer.write(frame(encrypted))
        await self.writer.drain()

    async def recv(self):
        encrypted = await receive_frame(self.reader)
        self.receive_sequence += 1
        return crypto_secretbox_open(encrypted, self.nonce(self.receive_sequence), self.key)

    async def close(self):
        self.writer.close()
        await self.writer.wait_closed()


async def connect_secure(port):
    reader, writer = await asyncio.open_connection(IP, port)
    exchange = await receive_frame(reader)
    outer = dict(parse_fields(exchange))
    signed_key = dict(parse_fields(outer[25]))[1]
    server_ephemeral = crypto_sign_open(signed_key, SERVER_PUBLIC_KEY)
    client_public, client_secret = crypto_box_keypair()
    symmetric_key = os.urandom(32)
    sealed_key = crypto_box(symmetric_key, bytes(24), server_ephemeral, client_secret)
    response = field(25, field(1, client_public) + field(1, sealed_key))
    writer.write(frame(response))
    await writer.drain()
    return SecureConnection(reader, writer, symmetric_key)


async def authenticate(port, role):
    connection = await connect_secure(port)
    challenge = await connection.recv()
    assert challenge.startswith(PREFIX + bytes([role])) and len(challenge) == len(PREFIX) + 33
    signature = RSA_KEY.sign(challenge, padding.PKCS1v15(), hashes.SHA256())
    await connection.send(signature)
    assert await connection.recv() == b"OK"
    return connection, signature


async def rejected(connection):
    try:
        await asyncio.wait_for(connection.recv(), 20)
    except (asyncio.IncompleteReadError, ConnectionError, ValueError, asyncio.TimeoutError):
        return
    raise AssertionError("unauthorized connection remained open")


async def run(work, processes):
    allowed = work / "technicians"
    allowed.mkdir()
    cert_path = allowed / "technician.cer"
    valid_certificate = certificate()
    cert_path.write_bytes(valid_certificate.public_bytes(serialization.Encoding.DER))
    base = 42116
    server_secret = base64.b64encode(SERVER_SECRET_KEY).decode()
    for name, port in [("hbbs", base), ("hbbr", base + 1)]:
        env = dict(os.environ, TECHNICIAN_WHITELIST_DIR=str(allowed), DB_URL=str(work / "db.sqlite3"),
                   HTTP_PROXY="http://127.0.0.1:1", HTTPS_PROXY="http://127.0.0.1:1")
        executable = SERVER / "target/release" / (name + (".exe" if os.name == "nt" else ""))
        log_path = work / (name + ".log")
        log = log_path.open("wb")
        processes.append(subprocess.Popen([str(executable), "-b", IP, "-p", str(port), "-k", server_secret],
                         cwd=work, env=env, stdout=log, stderr=subprocess.STDOUT,
                         creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0)))
        for _ in range(100):
            assert processes[-1].poll() is None, log_path.read_text()
            try:
                reader, writer = await asyncio.open_connection(IP, port + 2)
                writer.close()
                await writer.wait_closed()
                break
            except OSError:
                await asyncio.sleep(.05)
        else:
            raise AssertionError("server did not start")

    for role, port in [(0, base + 2), (1, base + 3)]:
        connection, signature = await authenticate(port, role)
        await connection.close()
        replay = await connect_secure(port)
        await replay.recv()
        await replay.send(signature)
        await rejected(replay)
        print(f"PASS encrypted role {role}: valid signature accepted and replay rejected")

    cert_path.write_bytes(certificate(True).public_bytes(serialization.Encoding.DER))
    expired = await connect_secure(base + 2)
    challenge = await expired.recv()
    await expired.send(RSA_KEY.sign(challenge, padding.PKCS1v15(), hashes.SHA256()))
    await rejected(expired)
    cert_path.write_bytes(valid_certificate.public_bytes(serialization.Encoding.DER))
    print("PASS expired certificate rejected")

    session = str(uuid.uuid4())
    receiver_reader, receiver_writer = await asyncio.open_connection(IP, base + 1)
    technician, _ = await authenticate(base + 3, 1)
    receiver_writer.write(frame(relay_request(session, False)))
    await receiver_writer.drain()
    await technician.send(relay_request(session, True))
    await technician.send(b"technician to receiver")
    assert await receive_frame(receiver_reader) == b"technician to receiver"
    receiver_writer.write(frame(b"receiver to technician"))
    await receiver_writer.drain()
    assert await technician.recv() == b"receiver to technician"
    await technician.close()
    receiver_writer.close()
    await receiver_writer.wait_closed()
    print("PASS encrypted technician relay paired with raw receiver in both directions")

    raw_reader, raw_writer = await asyncio.open_connection(IP, base + 1)
    raw_writer.write(frame(relay_request(str(uuid.uuid4()), True)))
    await raw_writer.drain()
    assert await asyncio.wait_for(raw_reader.read(), 5) == b""
    raw_writer.close()
    await raw_writer.wait_closed()
    print("PASS raw TCP technician cannot bypass authentication")


with tempfile.TemporaryDirectory(prefix="rustdesk-cert-test-") as directory:
    running = []
    try:
        asyncio.run(run(Path(directory), running))
    finally:
        for process in running:
            process.terminate()
            process.wait(timeout=5)
