"""
ipcex_socket_secure.py  --  Hardened socket server and client
                             for the talk2stat architecture

Supplementary material for:
  "How to Talk to Your Programs: Interprocess Communication for
   Data Scientists", The American Statistician (Teacher's Corner)

This file extends the abridged server/client code (Listings 5 and 6
in the paper) with three security measures:

  1. Token authentication  -- the client sends a shared secret before
                               any code is submitted; the server uses
                               hmac.compare_digest (constant-time) to
                               prevent timing-based attacks.

  2. Connection timeout     -- conn.settimeout() drops idle or slow
                               clients automatically; the server never
                               blocks indefinitely waiting for input.

  3. Input-length check     -- messages larger than MAX_INPUT_BYTES are
                               rejected before being forwarded to the
                               interpreter.

USAGE
-----
  Set the shared token via an environment variable (do not hard-code it):

      export TALK2STAT_TOKEN="your-secret-token"

  Start the server in one terminal:

      python ipcex_socket_secure.py server

  Run a query from a client in another terminal (or from LaTeX via runcode):

      python ipcex_socket_secure.py client "1 + 1"

Requires: pexpect  (pip install pexpect)
"""

import sys
import os
import hmac
import socket
import pexpect

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------
HOST          = '127.0.0.1'
PORT          = 54345
PROMPTCHAR    = 'julia> '
MAX_INPUT_BYTES = 1024 * 1024          # 1 MB hard limit on incoming messages
AUTH_TIMEOUT  = 10                     # seconds to receive token from client
EXEC_TIMEOUT  = 60                     # seconds to wait for Julia output
IDLE_TIMEOUT  = 60                     # seconds before dropping idle client

# Retrieve the secret from the environment; never fall back to a guessable
# default in production.  The fallback here is for demonstration only.
SECRET_TOKEN  = os.environ.get('TALK2STAT_TOKEN', 'demo-token-change-me')


# ---------------------------------------------------------------------------
# Shared helper
# ---------------------------------------------------------------------------
def verify_token(received: bytes) -> bool:
    """Constant-time comparison to prevent timing side-channel attacks."""
    return hmac.compare_digest(received.strip(), SECRET_TOKEN.encode())


# ---------------------------------------------------------------------------
# Server
# ---------------------------------------------------------------------------
def run_server():
    """
    Spawns Julia, binds a socket, and serves requests authenticated by a
    shared token.  Each accepted connection must present the token as its
    first message before any code will be executed.
    """
    print(f'Starting Julia...')
    child = pexpect.spawn('julia -q --color=no --banner=no')
    child.expect(PROMPTCHAR, timeout=EXEC_TIMEOUT)
    print(f'Julia ready.  Binding {HOST}:{PORT} (PID {os.getpid()})')

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as srv:
        srv.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        try:
            srv.bind((HOST, PORT))
        except OSError as exc:
            print(f'Cannot bind {HOST}:{PORT} -- {exc}')
            print('Another process may already be using this port.')
            return

        srv.listen()
        keepgoing = True

        while keepgoing:
            try:
                conn, addr = srv.accept()
            except KeyboardInterrupt:
                print('\nShutting down.')
                break

            with conn:
                # --- Step 1: authenticate --------------------------------
                conn.settimeout(AUTH_TIMEOUT)
                try:
                    token_received = conn.recv(4096)
                except socket.timeout:
                    print(f'Auth timeout from {addr}; closing.')
                    continue

                if not verify_token(token_received):
                    conn.sendall(b'AUTH_FAILED')
                    print(f'Bad token from {addr}; connection rejected.')
                    continue

                conn.sendall(b'AUTH_OK')

                # --- Step 2: serve requests from this authenticated client
                conn.settimeout(IDLE_TIMEOUT)
                buffer = []

                while True:
                    try:
                        raw = conn.recv(MAX_INPUT_BYTES)
                    except socket.timeout:
                        print(f'Idle timeout from {addr}; closing.')
                        break

                    if not raw:
                        break

                    # --- Step 3: validate input length --------------------
                    if len(raw) >= MAX_INPUT_BYTES:
                        conn.sendall(b'ERROR: input exceeds size limit\nEND')
                        continue

                    user_input = raw.decode(errors='replace')

                    if user_input.endswith('QUIT'):
                        keepgoing = False
                        break

                    # Forward to Julia through the pipe
                    child.sendline(user_input)
                    try:
                        child.expect(PROMPTCHAR, timeout=EXEC_TIMEOUT)
                    except pexpect.TIMEOUT:
                        buffer.append('TIMED OUT')

                    buffer.append(child.before)
                    buffer.append('\nEND')
                    conn.sendall(''.join(buffer).encode())
                    buffer.clear()

    child.close()
    print('Server stopped.')


# ---------------------------------------------------------------------------
# Client
# ---------------------------------------------------------------------------
def run_client(code: str) -> bool:
    """
    Connects to the server, authenticates, sends Julia code, and prints the
    result.  Returns True on success, False if the server is unreachable or
    authentication fails.
    """
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.settimeout(10)
        try:
            s.connect((HOST, PORT))
        except (ConnectionRefusedError, socket.timeout):
            print(f'Server not available at {HOST}:{PORT}.')
            return False

        # --- Authenticate ------------------------------------------------
        s.sendall(SECRET_TOKEN.encode())
        try:
            response = s.recv(4096)
        except socket.timeout:
            print('No auth response from server.')
            return False

        if response != b'AUTH_OK':
            print('Authentication failed.')
            return False

        # --- Send code and collect response ------------------------------
        s.settimeout(EXEC_TIMEOUT + 10)   # allow time for Julia to evaluate
        s.sendall(code.rstrip().encode())

        resp = ''
        try:
            while not resp.endswith('END'):
                chunk = s.recv(MAX_INPUT_BYTES).decode(errors='replace')
                if not chunk:
                    break
                resp += chunk
        except socket.timeout:
            print('Timed out waiting for server response.')
            return False

        print(resp.rstrip('END\n'))
    return True


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------
if __name__ == '__main__':
    if len(sys.argv) < 2 or sys.argv[1] not in ('server', 'client'):
        print('Usage:')
        print('  python ipcex_socket_secure.py server')
        print('  python ipcex_socket_secure.py client "<julia code>"')
        sys.exit(1)

    if sys.argv[1] == 'server':
        run_server()
    else:
        code = sys.argv[2] if len(sys.argv) > 2 else '1 + 1'
        success = run_client(code)
        sys.exit(0 if success else 1)
