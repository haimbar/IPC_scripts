from multiprocessing import Process, Pipe
import numpy as np

# ipcex4.py  --  Adaptive parallel bootstrap (Python)
#
# Corresponds to Listing 4 ("Adaptive parallel bootstrap using pipes")
# in the paper. R equivalent: ipcex4.R
#
# Distributes bootstrap resampling across M worker
# processes, each connected to the parent by its own
# multiprocessing.Pipe(). Each worker repeatedly draws a batch of
# bootstrap replicate means and sends the batch back through the pipe;
# the parent pools the batches received so far, recomputes the
# interval's endpoints, and stops once they have changed by less than
# a tolerance from the previous round, replying on the same pipe with
# either "GO" (keep sampling) or "STOP". The pipe carries many round
# trips, not one -- unlike a fixed-B one-shot parallel map, this design
# lets the computation decide for itself when enough replicates have
# been drawn.

def bootstrap_worker(conn, data, batch_size):
    rng = np.random.default_rng(conn.recv())   # seed from parent
    while True:
        batch = [rng.choice(data, len(data), replace=True).mean()
                 for _ in range(batch_size)]
        conn.send(batch)           # stream a batch of replicate means
        if conn.recv() == "STOP":  # parent decides whether to continue
            break
    conn.close()

def adaptive_bootstrap(data, M=4, batch_size=50, tol=0.0005, max_batches=100):
    pipes   = [Pipe() for _ in range(M)]
    workers = []
    for i, (parent_conn, child_conn) in enumerate(pipes):
        p = Process(target=bootstrap_worker, args=(child_conn, data, batch_size))
        p.start()
        conn = parent_conn
        conn.send(i * 1000)        # distinct seed per worker
        workers.append((p, conn))

    all_stats, prev = [], None
    for round_num in range(1, max_batches + 1):
        for p, conn in workers:
            all_stats.extend(conn.recv())   # this round's batch
        lo, hi = np.percentile(all_stats, [2.5, 97.5])
        stable = prev is not None and max(abs(lo - prev[0]), abs(hi - prev[1])) < tol
        stop = stable or round_num == max_batches
        prev = (lo, hi)
        for p, conn in workers:
            conn.send("STOP" if stop else "GO")
        if stop:
            break

    for p, conn in workers:
        p.join()
    return lo, hi, len(all_stats), round_num

if __name__ == "__main__":
    np.random.seed(0)
    data = np.random.exponential(scale=2.0, size=1_000)
    lo, hi, n_total, n_rounds = adaptive_bootstrap(data, M=4)
    print(f"95% CI: [{lo:.3f}, {hi:.3f}]  "
          f"(half-width {(hi-lo)/2:.3f}, {n_total:,} replicates, "
          f"{n_rounds} rounds)")
