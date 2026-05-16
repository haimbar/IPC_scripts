def ring(num_proc, my_id, conn_s, conn_r, cpproc, cols, Aloc,Xloc,Yloc):
    for t in range(num_proc+1):
        if t == 0:
            w = np.matmul(Aloc, Xloc)
        else:
            conn_s.send(w)
            w = conn_r.recv()
            j = my_id - t
            if j <= 0:
                j += num_proc
            Yloc += w[range((j-1)*cpproc, j*cpproc)]
    print(f"{my_id} current value: {Yloc}")

if __name__ == "__main__":
        N = 12
        procs = 4
        cpproc = int(N/procs) # columns per processor
        a = 0.9*np.ones(N)
        x = np.ones(N)
        y = np.linspace(-0.5, 0.5, N)
        A = np.vander(a, N)
        conn_send = []
        conn_recv = []
        for i in range(procs):
                parent_conn, child_conn = Pipe()
                conn_send.append(child_conn)
                conn_recv.append(parent_conn)
        for i in range(procs):
                cols = range(i*cpproc, (i+1)*cpproc)
                p = Process(target=ring, args=(procs, i, conn_send[i], conn_recv[(i+1)%procs], cpproc, cols, A[:, cols], x[cols], y[cols]))
                p.start()
