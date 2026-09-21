"""
ipcex_socket_secure.py -- A hardened version of the minimal socket
server/client shown in the paper's "Sockets" subsection (Section 2.4).

Supplementary material for:
  "How to Talk to Your Programs: A Practical Introduction to
   Interprocess Communication for Data Scientists"

The paper's minimal example is deliberately bare: it shows only
bind/listen/accept/connect and a single send/recv exchange. Before
exposing a socket server to anything beyond a trusted, single-user
localhost connection, the paper recommends three additions, all
implemented here:

  1. Token authentication -- the client sends a shared secret as its
     first message; the server checks it with hmac.compare_digest
     (constant-time, to avoid a timing side channel) before accepting
     any further input.
  2. Connection timeouts -- conn.settimeout() ensures the server never
     blocks indefinitely on a slow or unresponsive client.
  3. Input-length validation -- messages larger than MAX_INPUT_BYTES
     are rejected before being processed.

USAGE
-----
  Set the shared secret (do not hard-code it in real use):

      export IPC_DEMO_TOKEN="your-secret-token"

  Start the server in one terminal:

      python ipcex_socket_secure.py server

  Run the client in another terminal:

      python ipcex_socket_secure.py client

Requires: standard library only.
"""

import sys
import os
import hmac
import socket

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------
HOST            = '127.0.0.1'
PORT            = 6000
MAX_INPUT_BYTES = 1024          # reject anything larger
AUTH_TIMEOUT    = 10            # seconds to receive the token
IDLE_TIMEOUT    = 60            # seconds before dropping an idle client

# Retrieve the secret from the environment; never fall back to a
# guessable default in production. The fallback here is for
# demonstration only.
SECRET_TOKEN = os.environ.get('IPC_DEMO_TOKEN', 'demo-token-change-me')


def verify_token(received: bytes) -> bool:
    """Constant-time comparison to prevent timing side-channel attacks."""
    return hmac.compare_digest(received.strip(), SECRET_TOKEN.encode())


# ---------------------------------------------------------------------------
# Server
# ---------------------------------------------------------------------------
def run_server():
    """
    Binds a socket and serves a single authenticated request, guarded
    by connection timeouts and an input-length check, then exits --
    the same 'hello' / 'ack' exchange as the paper's minimal example,
    hardened.
    """
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        s.bind((HOST, PORT))
        s.listen()
        print(f'Listening on {HOST}:{PORT} (PID {os.getpid()})')

        conn, addr = s.accept()
        with conn:
            # --- Step 1: authenticate ---------------------------------
            conn.settimeout(AUTH_TIMEOUT)
            try:
                token_received = conn.recv(4096)
            except socket.timeout:
                print(f'Auth timeout from {addr}; closing.')
                return

            if not verify_token(token_received):
                conn.sendall(b'AUTH_FAILED')
                print(f'Bad token from {addr}; connection rejected.')
                return

            conn.sendall(b'AUTH_OK')

            # --- Step 2: serve the request, guarded by an idle timeout
            conn.settimeout(IDLE_TIMEOUT)
            try:
                data = conn.recv(MAX_INPUT_BYTES + 1)
            except socket.timeout:
                print(f'Idle timeout from {addr}; closing.')
                return

            # --- Step 3: validate input length -------------------------
            if len(data) > MAX_INPUT_BYTES:
                conn.sendall(b'ERROR: input exceeds size limit')
                print(f'Oversized input from {addr}; rejected.')
                return

            print(conn.getpeername(), '->', data.decode())  # 'hello'
            conn.sendall(b'ack')

    print('Server stopped.')


# ---------------------------------------------------------------------------
# Client
# ---------------------------------------------------------------------------
def run_client() -> bool:
    """
    Connects to the server, authenticates with the shared token, then
    sends 'hello' and prints the server's reply. Returns True on
    success, False if the server is unreachable or authentication
    fails.
    """
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.settimeout(10)
        try:
            s.connect((HOST, PORT))
        except (ConnectionRefusedError, socket.timeout):
            print(f'Server not available at {HOST}:{PORT}.')
            return False

        s.sendall(SECRET_TOKEN.encode())
        try:
            response = s.recv(4096)
        except socket.timeout:
            print('No auth response from server.')
            return False

        if response != b'AUTH_OK':
            print('Authentication failed.')
            return False

        s.sendall(b'hello')
        print(s.recv(1024).decode())      # 'ack'
    return True


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------
if __name__ == '__main__':
    if len(sys.argv) != 2 or sys.argv[1] not in ('server', 'client'):
        print('Usage:')
        print('  python ipcex_socket_secure.py server')
        print('  python ipcex_socket_secure.py client')
        sys.exit(1)

    if sys.argv[1] == 'server':
        run_server()
    else:
        sys.exit(0 if run_client() else 1)
