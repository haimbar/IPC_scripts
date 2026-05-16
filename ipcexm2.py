import signal, os, time
from functools import partial

# Second example: a program contains a loop which can run for a long time.
# Printing each iteration number will make the program much slower.
# We can define a signal which the loop will catch and print the iteration
# number only on-demand.
# In this case, we send the signal from a shell or from another
# program. From the shell, it will look like this:
# kill -s SIGUSR1 pid
# where pid is obtained when the program starts.

pid = os.getpid()
print(pid)


def checkstatus(itnum, signum, frame):
    print(f'Iteration number={itnum}')


# Simulate something that runs many times, and possibly each iteration
# takes a long time:
def longloop(k=10):  
    ctr = 0
    while ctr < k:
        signal.signal(signal.SIGUSR1, partial(checkstatus, ctr))
        ctr += 1
        time.sleep(3)
    print(f'Finished {ctr} iterations')

longloop() # while it's running, send a SIGUSR1 signal from the shell
