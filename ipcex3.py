import signal, os, time
from functools import partial
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

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

# The following sequence does not converge (it bifurcates), so the convergence criterion is never satisfied:
def nolimitseq(rt=3.1, k=1e6, eps=1e-5):
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

nolimitseq() # while it's running, send a USR1 signal from a terminal
