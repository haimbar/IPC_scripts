import signal, os
def someloop():
    # What to do if SIGALRM is received:
    signal.signal(signal.SIGALRM, handle_to)
    # Set a timer to send SIGALRM in 5 sec.:
    signal.alarm(5)
    # To demonstrate SIGALRM, we create an
    # infinite loop:
    while True:
        pass
    signal.alarm(0)  # Disable the alarm

def handle_to(signum, frame):
    signame = signal.Signals(signum).name
    print(f'Something went wrong.  Got {signame} ({signum}) Aborting!')
    exit(0)

someloop()
