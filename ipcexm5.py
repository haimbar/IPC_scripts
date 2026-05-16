from time import sleep
import sys
# from termcolor import colored

# print(colored('hello', 'red'), colored('world', 'green'))

# line_1 = "You have woken up in a mysterious maze"

# for x in line_1:
#     print(x, end='')
#     sys.stdout.flush()
#     sleep(0.1)

import matplotlib.pyplot as plt
import numpy as np

y = [np.nan]*20
plt.ion()
for i in range(20):
    y[i] = i**0.5 #np.random.random([1,1])
    plt.plot(y)
    plt.draw()
    plt.pause(1)
    plt.clf()

