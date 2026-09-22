# IPC Scripts

Supplementary code for:

> "How to Talk to Your Programs: A Practical Introduction to Interprocess
> Communication for Data Scientists," *The American Statistician*
> (Teacher's Corner).

Each numbered example is implemented once in Python and once in R. The two
files share a number and cover the same idea, but are not always literal
translations of each other: where the languages expose IPC primitives
differently (e.g., R has no user-level `SIGUSR1` handler), the R script
uses the idiomatic R equivalent instead, and its header comment explains
the substitution.

| # | Python | R | Topic |
|---|--------|---|-------|
| 1 | [`ipcex1.py`](ipcex1.py) | [`ipcex1.R`](ipcex1.R) | Setting a timeout for a function with `SIGALRM` (R: `setTimeLimit()`) |
| 2 | [`ipcex2.py`](ipcex2.py) | [`ipcex2.R`](ipcex2.R) | On-demand trace plots for an MCMC sampler via `SIGUSR1` (R: a polled flag file) |
| 3 | [`ipcex3.py`](ipcex3.py) | [`ipcex3.R`](ipcex3.R) | Dynamic load balancing across worker processes with `SIGCHLD` (R: `mclapply(mc.preschedule = FALSE)`) |
| 4 | [`ipcex4.py`](ipcex4.py) | [`ipcex4.R`](ipcex4.R) | Adaptive bootstrap confidence intervals over a persistent pipe (R: a persistent PSOCK cluster) |

`ipcex_socket_secure.py` is a standalone companion script referenced in the
paper's discussion of sockets; it is not part of the numbered pairs above.

## Requirements

- **Python**: standard library only, plus NumPy and Matplotlib (examples
  3 and 4 also use `multiprocessing`, which is part of the standard
  library).
- **R**: base R only, except `ipcex3.R` and `ipcex4.R`, which use the
  `parallel` package (included with base R).

## Running the examples

Each script is self-contained and runnable directly:

```bash
python3 ipcex1.py
Rscript ipcex1.R
```

Examples 1, 2, and 3 print instructions for interacting with the running
process from a second terminal (sending a signal or creating a flag
file); example 4 runs to completion on its own and prints the resulting
confidence interval.

## Scope

The examples target Linux and macOS. Windows users can run them under the
Windows Subsystem for Linux (WSL2).
