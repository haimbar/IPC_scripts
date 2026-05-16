keepgoing = True
promptchar = 'julia> '
child = pexpect.spawn('julia -q --color=no --banner=no')
child.expect(promptchar, timeout=60)
with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        try:
            s.bind(('127.0.0.1', 54345))
        except:
            return False
        s.listen()
        while keepgoing: 
            conn, addr = s.accept()
            with conn:
                buffer = []
                while True:
                    user_input = conn.recv(1024*1024).decode()
                    if user_input.endswith("QUIT"):
                        keepgoing = False
                        break
                    child.sendline(user_input)
                    try: 
                        child.expect(promptchar, timeout=60)
                    except pexpect.TIMEOUT:
                        buffer.append("TIMED OUT")
                    buffer.append(child.before)
                    buffer.append("\nEND")
                    buftmp = ''.join(buffer)
                    conn.sendall(buftmp.encode())
    child.close()
