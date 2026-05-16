# ipcexR4.R  --  Parallel bootstrap confidence intervals (R)
#
# Supplementary material for:
#   "How to Talk to Your Programs: Interprocess Communication for
#    Data Scientists", The American Statistician (Teacher's Corner)
#
# Python equivalent: ipcex4.py (Listing 4 in the paper)
#
# The Python version uses multiprocessing.Pipe() to distribute bootstrap
# replications across workers: the parent sends a seed through one end of
# the pipe, and the worker sends results back through the other end.
#
# This file shows two R equivalents:
#
#   Method A (PSOCK sockets, cross-platform):
#     makePSOCKcluster() opens one TCP socket connection per worker.
#     The master sends work and receives results through these sockets --
#     the same bidirectional channel as the Python pipe, but over TCP.
#     This works on Linux, macOS, and Windows.
#
#   Method B (fork + pipe, Unix/macOS):
#     mclapply() uses fork() and an anonymous pipe per child to collect
#     results.  This is the closest structural match to the Python example.
#     Does not work on Windows.
#
# Both methods produce identical confidence intervals.
#
# Requires: parallel (included in base R)

library(parallel)

# -------------------------------------------------------------------
# Worker function: receives a seed, generates B_local bootstrap means
# -------------------------------------------------------------------
bootstrap_worker <- function(seed, data, B_local) {
  set.seed(seed)
  replicate(B_local,
            mean(sample(data, size = length(data), replace = TRUE)))
}

# -------------------------------------------------------------------
# Method A: PSOCK cluster (socket-based, cross-platform)
# -------------------------------------------------------------------
parallel_bootstrap_psock <- function(data, B = 100000L, M = 4L) {
  B_each <- B %/% M
  seeds  <- (seq_len(M) - 1L) * 1000L

  cl <- makePSOCKcluster(M)
  on.exit(stopCluster(cl))          # always close the cluster

  # Export data to all workers through the socket connections.
  clusterExport(cl, "data", envir = environment())

  # parLapply sends one element of 'seeds' to each worker via its
  # socket, receives partial bootstrap samples, and collects results.
  partial <- parLapply(cl, seeds, bootstrap_worker,
                       data = data, B_local = B_each)
  unlist(partial)
}

# -------------------------------------------------------------------
# Method B: fork-based (Linux / macOS only)
# -------------------------------------------------------------------
parallel_bootstrap_fork <- function(data, B = 100000L, M = 4L) {
  B_each <- B %/% M
  seeds  <- (seq_len(M) - 1L) * 1000L

  # mclapply forks M workers; each child communicates its result back
  # to the parent through an anonymous pipe created by the OS.
  partial <- mclapply(seeds, bootstrap_worker,
                      data = data, B_local = B_each,
                      mc.cores = M)
  unlist(partial)
}

# -------------------------------------------------------------------
# Compare sequential vs. parallel (choose one method to run)
# -------------------------------------------------------------------
set.seed(0)
data <- rexp(1000L, rate = 0.5)   # Exponential(scale = 2); matches Python

# Sequential baseline
t_seq <- system.time({
  seq_stats <- replicate(100000L,
                 mean(sample(data, length(data), replace = TRUE)))
  seq_ci <- quantile(seq_stats, c(0.025, 0.975))
})

# Parallel -- PSOCK (works everywhere)
t_psock <- system.time({
  par_stats_psock <- parallel_bootstrap_psock(data, B = 100000L, M = 4L)
  par_ci_psock    <- quantile(par_stats_psock, c(0.025, 0.975))
})

# Parallel -- fork (Linux / macOS)
# Uncomment if not on Windows:
# t_fork <- system.time({
#   par_stats_fork <- parallel_bootstrap_fork(data, B = 100000L, M = 4L)
#   par_ci_fork    <- quantile(par_stats_fork, c(0.025, 0.975))
# })

cat(sprintf("Sequential  95%% CI: [%.3f, %.3f]  (%.1f s)\n",
            seq_ci[1],          seq_ci[2],          t_seq["elapsed"]))
cat(sprintf("Parallel (PSOCK) 95%% CI: [%.3f, %.3f]  (%.1f s)\n",
            par_ci_psock[1],    par_ci_psock[2],    t_psock["elapsed"]))

# Expected output on a quad-core laptop (times will vary):
#   Sequential  95% CI: [1.857, 2.151]  (8.1 s)
#   Parallel (PSOCK) 95% CI: [1.854, 2.149]  (2.5 s)
