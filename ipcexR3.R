# ipcexR3.R  --  Dynamic load balancing (R)
#
# Supplementary material for:
#   "How to Talk to Your Programs: Interprocess Communication for
#    Data Scientists", The American Statistician (Teacher's Corner)
#
# Python equivalent: ipcex3.py (Listing 3 in the paper)
#
# The Python version uses os.fork() + SIGCHLD to implement dynamic task
# assignment: whenever a child finishes, the parent is notified via
# SIGCHLD and assigns the next task to the freed slot.
#
# R's parallel::mclapply() with mc.preschedule = FALSE implements the
# same policy through the same underlying mechanism (fork + SIGCHLD).
# With mc.preschedule = TRUE (the default), tasks are partitioned
# statically into mc.cores batches before any forking occurs -- that
# is the static-partition approach that leads to idle processors.
# Setting mc.preschedule = FALSE instead forks one process per task,
# capping concurrency at mc.cores, and starts the next task as soon
# as a slot opens.
#
# NOTE: mclapply() uses fork() and works on Linux and macOS only.
#       For a cross-platform (including Windows) alternative using
#       socket-based worker pools, see the commented-out section at
#       the bottom of this file.
#
# Requires: parallel (included in base R)

library(parallel)

M  <- 3L    # max concurrent processes
xs <- 0:11  # tasks: compute x^2 for each x

do_something <- function(x, M = 3L) {
  pid <- Sys.getpid()
  cat(sprintf("PID %d starting task x=%d\n", pid, x))
  Sys.sleep(M * (x %% M + 1L))   # simulate variable runtimes
  result <- x^2L
  cat(sprintf("PID %d finished: x^2=%d\n", pid, result))
  result
}

cat("=== Dynamic scheduling (mc.preschedule = FALSE) ===\n")
t_dynamic <- system.time({
  results_dynamic <- mclapply(
    xs, do_something, M = M,
    mc.cores       = M,
    mc.preschedule = FALSE   # dynamic: next free slot gets next task
  )
})
cat(sprintf("\nResults: %s\n", paste(unlist(results_dynamic), collapse = " ")))
cat(sprintf("Elapsed: %.1f s\n\n", t_dynamic["elapsed"]))

# For comparison, the static partition (default mc.preschedule = TRUE)
# would divide the 12 tasks into 3 fixed batches of 4 before forking.
# If one batch happens to contain all the slow tasks, the other workers
# finish early and sit idle until that batch is done.

# -------------------------------------------------------------------------
# Cross-platform (Windows / Linux / macOS) alternative using PSOCK sockets
# -------------------------------------------------------------------------
# PSOCK clusters use TCP socket connections between the master and workers,
# so they work on any platform.  Unlike mclapply(), work distribution here
# is managed by the master sending tasks through the sockets rather than by
# fork + SIGCHLD.  The scheduling is still dynamic: parLapply() sends one
# task at a time to each worker, so faster workers receive more tasks.
#
# cl <- makePSOCKcluster(M)
# clusterExport(cl, "M")
# results_psock <- parLapply(cl, xs, do_something, M = M)
# stopCluster(cl)
# cat("Results:", unlist(results_psock), "\n")
