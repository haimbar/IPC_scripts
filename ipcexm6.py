import numpy as np
import os
from multiprocessing import Process, Pipe, freeze_support


def ring(num_proc, my_id, conn_s, conn_r, cpproc, cols, Aloc, Xloc, Yloc):
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
#        main()
	N = 12
	procs = 4
	cpproc = int(N/procs) # columns per processor

	a = 0.9*np.ones(N)
	x = np.ones(N)
	y = np.linspace(-0.5, 0.5, N)
	A = np.vander(a, N)
	z = np.matmul(A, x) + y # true result, to check what we get from the distributed version
	print(z, "\n")

	conn_send = []
	conn_recv = []

	for i in range(procs):
		parent_conn, child_conn = Pipe()
		conn_send.append(child_conn)
		conn_recv.append(parent_conn)
    
#freeze_support()

	for i in range(procs):
    #print(i)
		cols = range(i*cpproc, (i+1)*cpproc)
    #p = Process(target=ring, args=(conn_send[i], conn_recv[(i+1)%procs], y[cols], procs, i))
		p = Process(target=ring, args=(procs, i, conn_send[i], conn_recv[(i+1)%procs], cpproc, cols, A[:, cols], x[cols], y[cols]))
		p.start()






### main process
##
##imTheFather = True
##children = []
##for  i in range(num_proc):
##    child = os.fork()
##    if child:
##        children.append(child)
##    else:
##        imTheFather = False
##        print(i)
##        os.waitpid(child, 0)
##        break
##
##sys.exit(0)
##    # i-th child:

#print(i)
##    cols = range(i*cpproc, (i+1)*cpproc)
##    if not os.path.exists(f"{i:03}"):
##        os.mkfifo(f"{i:03}")
##    else:
##        print(i)
#gaxpy(num_proc, i, (i-1)%num_proc, (i+1)%num_proc, cpproc, cols, A[:, cols], x[cols], y[cols])
##    else: # main process
##        pids[i] = pid


#print(pids)
#for i in range(num_proc):
#    os.unlink(f"{i:03}")



        
    
# CAREFUL: ps x | grep idlelib.run | cut -f1 -d" " | xargs kill


# https://stackoverflow.com/questions/55110733/python-multiprocessing-pipe-communication-between-processes
# https://docs.python.org/3/library/subprocess.html#replacing-os-popen-os-popen2-os-popen3
# https://docs.python.org/3/library/subprocess.html#subprocess.Popen.communicate

# https://stackoverflow.com/questions/16768290/understanding-popen-communicate
# https://www.gnu.org/software/coreutils/mkfifo
# https://www.howtoforge.com/linux-mkfifo-command/

# http://www.bx.psu.edu/~nate/pexpect/pexpect.html
# https://pexpect.readthedocs.io/en/stable/api/pexpect.html
# Windows comment: https://buildmedia.readthedocs.org/media/pdf/pexpect/latest/pexpect.pdf


##def f(conn):
##    conn.send([42, None, 'hello'])
##    conn.close()
##
##if __name__ == '__main__':
##    parent_conn, child_conn = Pipe()
##    p = Process(target=f, args=(child_conn,))
##    p.start()
##    print(parent_conn.recv())   # prints "[42, None, 'hello']"
##    p.join()

# https://docs.python.org/3/library/multiprocessing.html


##def ring(conn_r, conn_s, msg, procs, my_id):
##    conn_s.send(msg)
##    print(f"{my_id} Got: {conn_r.recv()}")


##def gaxpy(num_proc, my_id, left, right, cpproc, cols, Aloc, Xloc, Yloc):
##    for t in range(num_proc+1):
##        if t == 0:
##            w = np.matmul(Aloc, Xloc)
##        else:
####            print(' '.join(map(str, w)), file=open(f"{right:03}", 'w'))
##            fn = f"/Users/haim/Documents/GitHub/IPC/{left:03}"
##            cnt = 0
##            while not os.path.exists(fn):
##                time.sleep(0.5)
##                cnt+=1
##                if cnt>4:
##                    break
##            w = np.loadtxt(fn, delimiter=' ')
##            j = my_id - t
##            if j <= 0:
##                j += num_proc
##            Yloc += w[range(1+(j-1)*cpproc, j*cpproc+1)]
##    print(my_id, fn, file=open(f"res", 'a'))
####    print(' '.join(map(str, Yloc)), file=open(f"/Users/haim/Documents/GitHub/IPC/res{right:03}", 'w'))
##
##
