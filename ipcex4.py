import signal, os, time
import numpy as np
import pandas as pd

ctrs = np.array([0, 0]) 
# ctrs[0] is the number of running processes
# ctrs[1] is the number of completed tasks

xs = pd.Series(range(12))
M = 3

def do_something(x):
    mypid = os.getpid()
    print(f'Processor is doing something with {x} using PID {mypid}')
    # simulate different speeds:
    time.sleep(M*(x%M + 1)) 
    print(f'PID {mypid} finished. Got {x**2}')
    exit(0)

def update_ctrs(signum, frame):
    ctrs[0] -= 1
    ctrs[1] += 1

i = 0
while i < len(xs):  # main loop
    signal.signal(signal.SIGCHLD,  update_ctrs)
    if ctrs[0] < M:
        pid = os.fork()
        if pid == 0:
            do_something(xs[i])
        else:
            ctrs[0] += 1
        i += 1
    else:
        time.sleep(1)
        # Note that the sleep will be interrupted if SIGCHLD is received

# Some processes may still be running when we exit the while loop. We can add a condition to wait for all of them to finish before exiting the loop. For example:
while ctrs[0] > 0: # clean up loop
    signal.signal(signal.SIGCHLD, update_ctrs)
    time.sleep(1)
