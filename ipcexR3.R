# ipcexR3.R  --  Dynamic load balancing (R)
#
# Supplementary material for:
#   "How to Talk to Your Programs: Interprocess Communication for
#    Data Scientists", The American Statistician (Teacher's Corner)
#
# Python equivalent: ipcexm4.py (Listing 3 in the paper)
#
# The Python version forks M workers ONCE; each worker claims the next
# unclaimed task index for itself (protected by a lock) as soon as it
# is free, rather than the parent forking a fresh child per task.
# SIGCHLD is used only so the parent can tell, without polling, when
# all M workers have exited.
#
# R's parallel::mclapply() has no built-in equivalent of that
# persistent, self-serving worker pool: with mc.preschedule = FALSE it
# still forks a fresh child for each task (up to mc.cores at a time),
# rather than reusing a fixed pool -- more like the naive per-task-fork
# design the paper argues against than the pool in Listing 3. It is
# used here anyway because it is the standard, idiomatic R tool for
# dynamic (as opposed to static) task assignment, and it fixes the same
# underlying problem: with mc.preschedule = TRUE (the default), tasks
# are partitioned statically into mc.cores batches before any forking
# occurs -- the static-partition approach that leads to idle
# processors. Setting mc.preschedule = FALSE instead starts the next
# task as soon as a slot opens, so no processor sits idle while a
# batch mate is still working through a slow task.
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
