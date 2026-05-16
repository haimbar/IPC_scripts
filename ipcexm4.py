import signal, os, time
import numpy as np
import pandas as pd

# Example #4::
# A simple program to run processes in parallel (similar to resevoir sampling).
# The main process has N tasks which can be run independently and there are maxk
# processors, but dividing N into maxk may not be ideal, since one processor may
# get a set of items which take a lot longer to complete. Instead, the main program
# forks up to maxk processes, and assigns the next item on the list to the next
# available process.
# In this case, we use SIGCHLD which tells the parent process when a child has
# terminated. When this happens, update_ctrs increments the total number of completed
# tasks, and substracts one from the number of running processes (so in the
# next iteration, it knows that it can assign the next item).

ctrs = np.array([0, 0]) # 0=number of running processes, 1=number of processed tasks
xs = pd.Series(range(12))
maxk = 3

def do_something(x):
    mypid = os.getpid()
    print(f'Processor is doing something with {x} using PID {mypid}')
    time.sleep(maxk*(x%maxk + 1)) # to simulate different speeds
    print(f'PID {mypid} finished. Got {x**2}')
    exit(0)

def update_ctrs(signum, frame):
    ctrs[0] -= 1
    ctrs[1] += 1

i = 0
while i < len(xs):
    signal.signal(signal.SIGCHLD,  update_ctrs)
    if ctrs[0] < maxk:
        pid = os.fork()
        if pid == 0:
            do_something(xs[i])
        else:
            ctrs[0] += 1
        i += 1
    else:
        time.sleep(1)
        # Note that the sleep will be interrupted if SIGCHLD is received

# Some processes may stil be running when we exit the while loop. We can
# add a condition to wait for all of them to finish before exiting the loop.
# for example:
while ctrs[0] > 0:
    signal.signal(signal.SIGCHLD,  update_ctrs)
    time.sleep(1)

