import signal, os

# First example (adapted from the signal package documentation
# https://docs.python.org/3/library/signal.html )

# Implement a timeout for processes which may hang. Set a timer which
# will stop the program if it doesn't complete what it has to do within
# 5 seconds

pid = os.getpid()
print(f'PID={pid}')

# Set the signal handler and a 5-second alarm.
# In this example, the signal is sent to the handletimeout function
# from within the someloop function.
def someloop():
    signal.signal(signal.SIGALRM, handletimeout)
    signal.alarm(5)
    while True:
        pass
    # Disable the alarm
    signal.alarm(0)


# Define what to do when getting the ALRM signal
def handletimeout(signum, frame):
    signame = signal.Signals(signum).name
    print(f'Something went wrong. Got {signame} ({signum}) Aborting!')
    exit(0)


someloop()

print("Can now move on to the rest of the code")