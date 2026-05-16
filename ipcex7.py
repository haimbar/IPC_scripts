with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
    try:
        s.connect(('127.0.0.1', 54345))
    except ConnectionRefusedError:
        return False
    s.sendall(filename.rstrip().encode())
    resp = ""
    while not resp.endswith("END"):
        resp = resp + s.recv(1024*1024).decode()
    print(resp.rstrip("END\n"))
return True
