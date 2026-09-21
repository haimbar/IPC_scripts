import signal, os, numpy as np, matplotlib.pyplot as plt

# Example #7 (MCMC monitoring):
# On-demand trace plots for a Metropolis-Hastings sampler. Corresponds
# to Listing 2 ("On-demand trace plots for an MCMC sampler") in the
# paper. Send SIGUSR1 to the printed PID at any point while this is
# running to see a live trace plot; the sampler resumes right after.
#
# The SIGUSR1 handler (request_plot) does as little as possible: it
# sets a flag and returns. The actual plotting happens in the main
# sampling loop, which checks the flag once per iteration. Calling into
# matplotlib's GUI machinery directly from a signal handler is fragile
# (the handler can interrupt the program at an arbitrary point,
# including inside the GUI backend's own bookkeeping) and can produce
# a stale, unrefreshed plot on a second request on some platforms --
# see the paper for a fuller discussion.

pid = os.getpid()
print(f"PID {pid} -- in another terminal run: kill -s SIGUSR1 {pid}")

plot_requested = False

def request_plot(signum, frame):
    global plot_requested
    plot_requested = True   # minimal work; see discussion in the paper

def log_posterior(theta, y, sigma=1.0, mu0=0.0, tau=10.0):
    log_lik   = -0.5 * np.sum((y - theta)**2) / sigma**2
    log_prior = -0.5 * ((theta - mu0) / tau)**2
    return log_lik + log_prior

def plot_trace(chain, i):
    plt.ion()
    fig, ax = plt.subplots(figsize=(8, 3))
    ax.plot(chain[:i], lw=0.5, color='steelblue')
    ax.axhline(chain[:i].mean(), color='red', lw=1.5,
               label=f'running mean = {chain[:i].mean():.3f}')
    ax.set_title(f'Trace plot at iteration {i:,}')
    ax.set_xlabel('Iteration'); ax.set_ylabel(r'$\theta$')
    ax.legend(); plt.tight_layout()
    plt.show(block=False); plt.pause(3); plt.close('all')

def mh_sampler(y, n_iter=500_000, step=0.3):
    global plot_requested
    signal.signal(signal.SIGUSR1, request_plot)  # registered once
    chain      = np.empty(n_iter)
    theta, lp  = 0.0, log_posterior(0.0, y)
    for i in range(n_iter):
        if plot_requested:
            plot_trace(chain, i)
            plot_requested = False
        proposal = theta + np.random.normal(0, step)
        lp_prop  = log_posterior(proposal, y)
        if np.log(np.random.rand()) < lp_prop - lp:
            theta, lp = proposal, lp_prop
        chain[i] = theta
    return chain

if __name__ == "__main__":
    np.random.seed(42)
    y_obs = np.random.normal(loc=3.5, scale=1.0, size=100)
    chain = mh_sampler(y_obs)

    burned_in = chain[50_000:]
    print(f"Posterior mean: {burned_in.mean():.3f},  "
          f"95% CI: [{np.quantile(burned_in, 0.025):.3f}, "
          f"{np.quantile(burned_in, 0.975):.3f}]")
