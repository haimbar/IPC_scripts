# ipcexR2.R  --  On-demand trace plots for an MCMC sampler (R)
#
# Supplementary material for:
#   "How to Talk to Your Programs: Interprocess Communication for
#    Data Scientists", The American Statistician (Teacher's Corner)
#
# Python equivalent: ipcexm7.py (Listing 2 in the paper)
#
# In the Python version, the user sends a SIGUSR1 signal from a second
# terminal and the sampler's signal handler fires immediately.  R does
# not expose POSIX user-defined signal handlers (SIGUSR1/SIGUSR2) to
# user-level code, so we use a file-flag instead: the user creates a
# small trigger file from a second terminal, and the sampler checks for
# it every CHECK_EVERY iterations, then plots and deletes the file.
#
# The practical effect is identical: the user can request a trace plot
# at any point during the run without modifying or restarting the sampler.
# The only difference is latency: the response takes up to CHECK_EVERY
# iterations (default 200) rather than being truly instantaneous.
#
# Requires: base R only (no packages needed)

FLAG_FILE   <- "mcmc_trace.flag"   # create this file to request a plot
CHECK_EVERY <- 200L                # check for the flag every N iterations

# -------------------------------------------------------------------
# Statistical model:
#   y_i ~ N(theta, sigma^2),  sigma^2 = 1  (known)
#   theta ~ N(mu0=0, tau^2=100)
# -------------------------------------------------------------------
log_posterior <- function(theta, y, sigma = 1.0, mu0 = 0.0, tau = 10.0) {
  log_lik   <- -0.5 * sum((y - theta)^2) / sigma^2
  log_prior <- -0.5 * ((theta - mu0) / tau)^2
  log_lik + log_prior
}

plot_trace <- function(chain, i) {
  # Show the last min(i, 2000) values and the running mean.
  n_show <- min(i, 2000L)
  idx    <- seq.int(max(1L, i - n_show + 1L), i)
  plot(idx, chain[idx],
       type = "l", col = "steelblue", lwd = 0.5,
       xlab = "Iteration", ylab = expression(theta),
       main = sprintf("Trace plot at iteration %s  (running mean = %.3f)",
                      format(i, big.mark = ","), mean(chain[seq_len(i)])))
  abline(h = mean(chain[seq_len(i)]), col = "red", lwd = 1.5)
}

# -------------------------------------------------------------------
# Metropolis-Hastings sampler
# -------------------------------------------------------------------
mh_sampler <- function(y, n_iter = 500000L, step = 0.3) {
  chain  <- numeric(n_iter)
  theta  <- 0.0
  lp     <- log_posterior(theta, y)

  cat(sprintf(
    "Sampler running (PID %d).\n", Sys.getpid()))
  cat("For a trace plot, open another terminal and run:\n")
  cat(sprintf(
    "   touch %s\n", FLAG_FILE))
  cat(sprintf(
    "The sampler checks every %d iterations.\n\n", CHECK_EVERY))

  for (i in seq_len(n_iter)) {
    proposal <- theta + rnorm(1L, 0, step)
    lp_prop  <- log_posterior(proposal, y)
    if (log(runif(1L)) < lp_prop - lp) {
      theta <- proposal
      lp    <- lp_prop
    }
    chain[i] <- theta

    # Check for on-demand trace-plot request every CHECK_EVERY iterations.
    if (i %% CHECK_EVERY == 0L && file.exists(FLAG_FILE)) {
      file.remove(FLAG_FILE)
      dev.new(width = 8, height = 3)
      plot_trace(chain, i)
      Sys.sleep(3)
      dev.off()
    }
  }
  chain
}

# -------------------------------------------------------------------
# Run the sampler
# -------------------------------------------------------------------
set.seed(42)
y_obs  <- rnorm(100L, mean = 3.5, sd = 1.0)   # true theta = 3.5
chain  <- mh_sampler(y_obs)

burned_in <- chain[50001L:length(chain)]
cat(sprintf("Posterior mean : %.3f\n",   mean(burned_in)))
cat(sprintf("95%% credible interval: [%.3f, %.3f]\n",
            quantile(burned_in, 0.025),
            quantile(burned_in, 0.975)))
