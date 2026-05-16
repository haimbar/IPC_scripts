# ipcexR1.R  --  Setting a timeout for a function (R)
#
# Supplementary material for:
#   "How to Talk to Your Programs: Interprocess Communication for
#    Data Scientists", The American Statistician (Teacher's Corner)
#
# Python equivalent: ipcex1.py (Listing 1 in the paper)
#
# R does not expose POSIX signal handlers directly, but setTimeLimit()
# achieves the same effect: on Unix/macOS it uses SIGALRM internally;
# on Windows it uses a thread-based timer.  Either way, exceeding the
# limit raises an R error condition that can be caught with tryCatch().
#
# Requires: base R only (no packages needed)

run_with_timeout <- function(timeout_secs = 5) {
  # Register the time limit BEFORE entering the potentially hanging code.
  # transient = TRUE means the limit is cleared once this call returns.
  setTimeLimit(elapsed = timeout_secs, transient = TRUE)

  cat(sprintf("Running with a %d-second timeout...\n", timeout_secs))

  tryCatch({
    repeat {}   # simulates an operation that never finishes
    setTimeLimit(elapsed = Inf)   # reset if we finish early (not reached here)
  }, error = function(e) {
    # setTimeLimit() raises an error whose message contains "time limit"
    cat("Caught timeout error:", conditionMessage(e), "\n")
    cat("Aborting cleanly.\n")
  })

  # Always reset after use so later calls are not affected.
  setTimeLimit(elapsed = Inf)
}

run_with_timeout(timeout_secs = 5)

# -------------------------------------------------------------------------
# Alternative: R.utils::withTimeout()
# If the R.utils package is installed, a more explicit interface is:
#
#   library(R.utils)
#   withTimeout({
#     repeat {}
#   }, timeout = 5, onTimeout = "error")
#
# withTimeout() is a wrapper around setTimeLimit() with a cleaner API.
# -------------------------------------------------------------------------
