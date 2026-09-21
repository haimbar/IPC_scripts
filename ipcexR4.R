# ipcexR4.R  --  Adaptive bootstrap confidence intervals (R)
#
# Supplementary material for:
#   "How to Talk to Your Programs: Interprocess Communication for
#    Data Scientists", The American Statistician (Teacher's Corner)
#
# Python equivalent: ipcexm8.py (Listing 4 in the paper)
#
# The Python version keeps each worker alive for the whole computation,
# connected to the parent by its own multiprocessing.Pipe(): a worker
# repeatedly draws a batch of bootstrap replicate means and sends it
# back, and the parent replies with "GO" or "STOP" once it has checked
# whether the confidence interval has stabilized. The point is an
# ongoing conversation over a channel that stays open, not a single
# round-trip or a fixed-B one-shot parallel map.
#
# A parallel::makePSOCKcluster() is the R analogue of that persistent
# channel: each worker's R session stays alive across repeated calls to
# parLapply(), so state set up once (the data, the per-worker RNG
# stream) persists between rounds, the same way the Python workers'
# local state persists between messages on their pipe. Each parLapply()
# call is one round of the conversation; the master decides whether to
# call it again -- the same adaptive stopping rule as the Python
# version, expressed as a loop instead of explicit "GO"/"STOP"
# messages, since parLapply() already blocks until every worker has
# replied for that round.
#
# Requires: parallel (included in base R)

library(parallel)

# -------------------------------------------------------------------
# Worker-side function: draws one batch of bootstrap replicate means.
# 'data' persists on each worker (exported once, below); the worker's
# RNG stream also persists across rounds because each worker is a
# long-lived R session, not a fresh process per call.
# -------------------------------------------------------------------
bootstrap_batch <- function(batch_size) {
  replicate(batch_size,
            mean(sample(data, length(data), replace = TRUE)))
}

# -------------------------------------------------------------------
# Parent side: opens the persistent cluster, seeds each worker once,
# then repeats rounds of "collect a batch from everyone, check
# stability, decide whether to continue" until the estimated interval
# stops moving or max_rounds is reached.
# -------------------------------------------------------------------
adaptive_bootstrap <- function(data, M = 4L, batch_size = 50L,
                                tol = 0.0005, max_rounds = 100L) {
  cl <- makePSOCKcluster(M)
  on.exit(stopCluster(cl))          # always close the cluster

  # Export the data once, and seed each worker once, exactly as the
  # Python version sends one seed per worker before the round loop
  # begins.
  clusterExport(cl, "data", envir = environment())
  clusterApply(cl, (seq_len(M) - 1L) * 1000L, function(s) set.seed(s))

  all_stats <- numeric(0)
  prev <- NULL
  for (round_num in seq_len(max_rounds)) {
    batches   <- parLapply(cl, rep(batch_size, M), bootstrap_batch)
    all_stats <- c(all_stats, unlist(batches))     # this round's batches
    ci        <- quantile(all_stats, c(0.025, 0.975))
    stable    <- !is.null(prev) &&
      max(abs(ci[1] - prev[1]), abs(ci[2] - prev[2])) < tol
    prev <- ci
    if (stable || round_num == max_rounds) break
  }
  list(ci = ci, n_total = length(all_stats), n_rounds = round_num)
}

# -------------------------------------------------------------------
# Run it
# -------------------------------------------------------------------
set.seed(0)
data <- rexp(1000L, rate = 0.5)   # Exponential(scale = 2); matches Python

result <- adaptive_bootstrap(data, M = 4L)
cat(sprintf(
  "95%% CI: [%.3f, %.3f]  (half-width %.3f, %d replicates, %d rounds)\n",
  result$ci[1], result$ci[2],
  (result$ci[2] - result$ci[1]) / 2,
  result$n_total, result$n_rounds))
