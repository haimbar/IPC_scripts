import signal, os, time
import multiprocessing as mp
import numpy as np

# ipcex3.py  --  Dynamic load balancing (Python)
#
# Corresponds to Section 3.3 / Listing 3 in the paper.
# R equivalent: ipcex3.R
#
# Each task is a first-passage-time random walk: it runs until it
# first crosses +/-L, where L stands in for something like gene length
# in the paper's motivating example (comparing pairs of strings costs
# roughly L**2, and most genes are short but a few are much longer).
# Because a task's runtime is unknown until it actually runs, no
# static partition of the task list -- however carefully chosen -- can
# balance the load in advance.
#
# Two dispatch policies are compared below on the *same* list of
# tasks, so the difference in wall-clock time isolates the effect of
# the dispatch policy itself:
#
#   run_static(xs, M)   The naive approach: split the N tasks into M
#                       equal, contiguous batches and fork one child
#                       per batch up front. Whichever batch happens to
#                       contain the long tasks sets the total runtime;
#                       the other workers sit idle once their batch is
#                       done.
#
#   run_dynamic(xs, M)  Listing 3 in the paper. Fork M workers ONCE;
#                       each worker claims the next unclaimed task
#                       index for itself (protected by a lock) as soon
#                       as it is free, instead of the parent forking a
#                       fresh child per task. SIGCHLD is used only so
#                       the parent can tell, without polling, when all
#                       M workers have exited -- not to trigger a new
#                       fork, since there isn't one.
#
# The SIGCHLD handler below reaps every child that has exited so far
# with a WNOHANG loop, rather than assuming one signal means exactly
# one exited child: if several children exit close together, the OS
# may coalesce their SIGCHLD notifications into a single delivery, and
# a handler that just does `finished += 1` per call can undercount.


LONG_BLOCK = range(119, 135)  # a run of 16 "long gene" tasks, one short
                               # of a full static worker's share -- not at
                               # the end of the list (see paper: this is
                               # what lets a long task block short ones
                               # queued behind it in a static partition,
                               # not just idle other workers)


def barrier_for(x):
    rng = np.random.default_rng(636 + x)
    if x in LONG_BLOCK:
        return rng.uniform(13, 17)
    return rng.uniform(2, 4)


def random_walk(x):
    L = barrier_for(x)
    rng = np.random.default_rng(x)
    pos, steps = 0.0, 0
    while abs(pos) < L:
        pos += rng.normal()
        time.sleep(0.012)         # simulate per-step computation
        steps += 1
    print(f'PID {os.getpid()} finished task x={x}: '
          f'absorbed after {steps} steps (L={L:.1f})', flush=True)


def run_static(xs, M):
    n = len(xs)
    chunk = (n + M - 1) // M
    pids = []
    for m in range(M):
        pid = os.fork()
        if pid == 0:
            for x in xs[m * chunk:(m + 1) * chunk]:
                random_walk(x)
            os._exit(0)
        pids.append(pid)
    for pid in pids:
        os.waitpid(pid, 0)


def run_dynamic(xs, M):
    n = len(xs)
    next_idx = mp.Value('i', 0)
    lock = mp.Lock()
    finished = mp.Value('i', 0)   # updated only by the parent's handler

    def on_child_done(signum, frame):
        while True:
            try:
                pid, _ = os.waitpid(-1, os.WNOHANG)
            except ChildProcessError:
                break
            if pid == 0:
                break
            finished.value += 1

    def worker_loop():
        while True:
            with lock:
                i = next_idx.value
                if i >= n:
                    break
                next_idx.value += 1
            random_walk(xs[i])
        os._exit(0)

    signal.signal(signal.SIGCHLD, on_child_done)
    for _ in range(M):
        if os.fork() == 0:
            worker_loop()

    while finished.value < M:
        time.sleep(1)              # interrupted immediately by SIGCHLD


if __name__ == "__main__":
    xs = list(range(255))
    M = 15

    t0 = time.time()
    run_static(xs, M)
    t_static = time.time() - t0
    print(f"\nstatic partition:  {t_static:.1f} s (M={M})\n", flush=True)

    t0 = time.time()
    run_dynamic(xs, M)
    t_dynamic = time.time() - t0
    print(f"\ndynamic dispatch:  {t_dynamic:.1f} s (M={M})")
    print(f"speedup: {t_static / t_dynamic:.2f}x")
