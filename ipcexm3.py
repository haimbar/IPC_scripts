import signal, os, time
from functools import partial
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt


# Third example: the program aims to find a solution to a difference
# [https://www.youtube.com/watch?v=ovJcsL7vyrk][equation], which doesn't
# converge. We define a handler to catch a signal,  and show the last 30
# steps of the sequence.
# In this case, we send the signal from a shell or from another program.
# From the shell, it will look like this
#   kill -s SIGUSR1 pid
# where pid is obtained when the program starts:

pid = os.getpid()
print(pid)


def plotstatus(ctr, xs, signum, frame):
    plt.ion()
    print(f'Iteration {ctr}')
    a = pd.Series(xs)
    plt.plot(a)
    plt.title(f'Up to iteration #{ctr}')
    plt.show(block=False)
    plt.pause(3)
    plt.close('all')


# Simulate something that runs many times, and possibly each iteration
# takes a long time:
def nolimitsequence(rt=3.1, k=1000000, eps=1e-5):
    xs = [0.6]*k
    xs[0] = 0.4
    ctr = 1
    while abs(xs[ctr]-xs[ctr-1]) > eps:
        signal.signal(signal.SIGUSR1, partial(plotstatus, ctr, xs[max(0,ctr-30):ctr]))
        xs[ctr] = rt*xs[ctr-1]*(1-xs[ctr-1])
        ctr += 1
        if ctr >= k:
            break
    print(f'Finished {ctr} iterations')

nolimitsequence() # while it's running, send a SIGUSR1 signal

