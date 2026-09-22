import signal, os

# ipcex1.py  --  Setting a timeout for a function (Python)
#
# Corresponds to Listing 1 ("Setting a timeout with SIGALRM") in the
# paper. R equivalent: ipcex1.R
#
# signal.alarm(5) asks the OS to deliver SIGALRM five seconds from
# now; signal.signal(...) registers handle_timeout to run when it
# arrives, replacing the OS default (silent process termination).
# Any signal except SIGKILL and SIGSTOP can be redirected this way.


def run_with_timeout():
    signal.signal(signal.SIGALRM, handle_timeout)
    signal.alarm(5)           # ask OS: send SIGALRM in 5 seconds
    while True:                # simulates a hanging operation
        pass
    signal.alarm(0)           # cancel alarm if we finish early


def handle_timeout(signum, frame):
    name = signal.Signals(signum).name
    print(f'Timed out ({name}). Aborting.')
    exit(1)


if __name__ == "__main__":
    print(f'PID {os.getpid()}')
    run_with_timeout()
