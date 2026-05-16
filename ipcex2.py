import signal, os, time
from functools import partial
pid = os.getpid()
print(pid) # show the process ID on the screen so that we can send it signals

def checkstatus(itnum, signum, frame):
    print(f'Iteration number={itnum}')

# Simulate something that either runs many times, or each iteration takes a long time:
def longloop(k=10):  
    ctr = 0
    while ctr < k:
        signal.signal(signal.SIGUSR1, partial(checkstatus, ctr))
        ctr += 1
        time.sleep(3)
    print(f'Finished {ctr} iterations')

longloop() # while it's running, send a USR1 signal from a terminal
