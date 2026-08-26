import os
import subprocess

os.environ["PATH"] = "/opt/homebrew/bin:" + os.environ["PATH"]

#function to run the c program from python
def compile_and_run_c(integrand, parameters):
    directory = "c-projects/hello/integrators/parallel-monte-carlo-c"
    #make clean
    subprocess.run(["make", "clean"], cwd=directory, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    #make with integrand
    subprocess.run(["make", f"FORMULA={integrand}"], cwd=directory, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    run_command = ["./integrate"] + parameters.split()
    #make with custom parameters
    run_result = subprocess.run(run_command, cwd=directory, capture_output=True, text=True, check=True)

    #print(run_result.stdout)
    for line in run_result.stdout.splitlines():
        if line.startswith("The integral value is: "):
            number_string = line.removeprefix("The integral value is: ").strip()
            integral_value = float(number_string)
    return integral_value

#if __name__ == "__main__":
 #   result = compile_and_run_c("pow(x, 5)", "16000000 8 0 1")
  #  print(result)

"""
Test suite for the parallel Monte Carlo integrator. THIS TEST SUITE WAS BUILT BY CLAUDE. All other
lines of code in this project were written by a human.

Assumes `compile_and_run_c(func_str, args_str)` is already defined/imported
in this file (it compiles + runs the C program and returns the final
numeric result as a float).

Command-line contract assumed (per the project spec):
    args_str = "N threads min max [seed] [integrand_max] [integrand_min]"

- N        : number of Monte Carlo samples
- threads  : number of worker threads
- min,max  : integration range [a, b]
- seed     : optional RNG seed (reproducibility)
- integrand_max, integrand_min : optional bounds on f(x) over [a,b]
  (only relevant if your scheme uses an envelope/hit-or-miss style method;
  ignore those sections below if your integrator doesn't use them)

NOTE ON FUNCTION STRINGS: no spaces allowed, e.g. "pow(x,5)" not "pow(x, 5)".

Ground truth for each test is computed with a pure-Python composite
Simpson's rule (no external dependencies), evaluated at high resolution,
so it should be accurate to many more digits than the Monte Carlo result.

Note: section 3 should be updated for an actual test, but takes a while to run
"""

import math

# =====================================================================
# Ground truth integrator (independent of the C code, used as reference)
# =====================================================================

def simpsons_rule(f, a, b, n=200_000):
    """Composite Simpson's rule. n must be even; bumped up automatically."""
    if a == b:
        return 0.0
    if n % 2 == 1:
        n += 1
    h = (b - a) / n
    total = f(a) + f(b)
    for i in range(1, n):
        x = a + i * h
        total += f(x) * (4 if i % 2 == 1 else 2)
    return total * h / 3.0


# =====================================================================
# Test bookkeeping
# =====================================================================

_pass_count = 0
_fail_count = 0
_error_count = 0


def check(name, c_func, py_func, samples, threads, a, b,
          seed=None, imax=None, imin=None, tol=0.03, note=""):
    """Run one test: build args string, call compile_and_run_c, compare to
    Simpson's-rule ground truth within relative tolerance `tol`."""
    global _pass_count, _fail_count, _error_count

    args = f"{samples} {threads} {a} {b}"
    if seed is not None:
        args += f" {seed}"
    if imax is not None:
        args += f" {imax}"
    if imin is not None:
        args += f" {imin}"

    exact = simpsons_rule(py_func, a, b)

    try:
        got = compile_and_run_c(c_func, args)
    except Exception as e:
        _error_count += 1
        print(f"[ERROR] {name}: exception during run -> {e}")
        return None, exact, False

    denom = abs(exact) if abs(exact) > 1e-12 else 1.0
    err = abs(got - exact) / denom
    passed = err <= tol

    if passed:
        _pass_count += 1
    else:
        _fail_count += 1

    tag = "PASS" if passed else "FAIL"
    extra = f"  ({note})" if note else ""
    print(f"[{tag}] {name}: got={got:.6f} exact={exact:.6f} "
          f"rel_err={err:.2%} tol={tol:.2%}{extra}")
    return got, exact, passed


def section(title):
    print()
    print("=" * 72)
    print(title)
    print("=" * 72)


# Global defaults you can dial down for a quick smoke test, or up for
# tighter statistical confidence.
DEFAULT_N = 5_000_000
DEFAULT_THREADS = 4


# =====================================================================
# SECTION 1: Basic correctness against known integrals
# =====================================================================

section("SECTION 1: Basic correctness")

check("x^5 on [0,1] (= 1/6)", "pow(x,5)", lambda x: x**5,
      DEFAULT_N, DEFAULT_THREADS, 0, 1)

check("x^2 on [0,2] (= 8/3)", "pow(x,2)", lambda x: x**2,
      DEFAULT_N, DEFAULT_THREADS, 0, 2)

check("odd function x^3 on [-1,1] (= 0)", "pow(x,3)", lambda x: x**3,
      DEFAULT_N, DEFAULT_THREADS, -1, 1, tol=0.02, note="tol is absolute-ish near 0, watch the ratio metric")

check("sin(x) on [0,pi] (= 2)", "sin(x)", math.sin,
      DEFAULT_N, DEFAULT_THREADS, 0, math.pi)

check("cos(x) on [0,pi/2] (= 1)", "cos(x)", math.cos,
      DEFAULT_N, DEFAULT_THREADS, 0, math.pi / 2)

check("exp(x) on [0,1] (= e-1)", "exp(x)", math.exp,
      DEFAULT_N, DEFAULT_THREADS, 0, 1)

check("sqrt(x) on [0,1] (= 2/3)", "sqrt(x)", math.sqrt,
      DEFAULT_N, DEFAULT_THREADS, 0, 1)

check("1/(1+x*x) on [0,1] (= pi/4)", "1/(1+x*x)", lambda x: 1 / (1 + x * x),
      DEFAULT_N, DEFAULT_THREADS, 0, 1)

check("log(x+1) on [0,1] (= 2ln2-1)", "log(x+1)", lambda x: math.log(x + 1),
      DEFAULT_N, DEFAULT_THREADS, 0, 1)

check("constant function 5 on [0,1] (= 5)", "x-x+5", lambda x: 5.0,
      DEFAULT_N, DEFAULT_THREADS, 0, 1, tol=0.01)


# =====================================================================
# SECTION 2: Thread-count consistency
# Same problem, same sample count, varying threads. All should converge
# to the correct value -- large deviations between thread counts hint
# at race conditions or bad work partitioning.
# =====================================================================

section("SECTION 2: Thread-count consistency (x^2 on [0,1], = 1/3)")

for t in [1, 2, 4, 8, 16, 32]:
    check(f"{t} thread(s)", "pow(x,2)", lambda x: x**2,
          4_000_000, t, 0, 1, seed=42)


# =====================================================================
# SECTION 3: Convergence with increasing N
# Monte Carlo error should shrink roughly like 1/sqrt(N). Increasing N
# by 10x should shrink the error by roughly sqrt(10) ~= 3.16x.
# =====================================================================

section("SECTION 3: Convergence rate check (sin(x) on [0,pi])")

exact_sin = simpsons_rule(math.sin, 0, math.pi)
#for a true test, this should be upped to 100
trials_per_N = 10
prev_avg_err = None

for n in [10_000, 100_000, 1_000_000, 10_000_000]:
    errs = []
    for i in range(trials_per_N):
        try:
            got = compile_and_run_c("sin(x)", f"{n} {DEFAULT_THREADS} 0 {math.pi} {3000+i}")
            errs.append(abs(got - exact_sin))
        except Exception as e:
            print(f"N={n:>10}, trial {i}: ERROR -> {e}")

    if not errs:
        print(f"N={n:>10}: all trials failed")
        continue

    avg_err = sum(errs) / len(errs)
    ratio_str = ""
    if prev_avg_err is not None and avg_err > 0:
        ratio_str = f"  error_ratio={prev_avg_err/avg_err:.2f} (expect ~3.16 for 10x N)"
    print(f"N={n:>10}: avg_abs_err over {trials_per_N} trials = {avg_err:.6f}{ratio_str}")
    prev_avg_err = avg_err

# =====================================================================
# SECTION 4: Seed reproducibility
# =====================================================================

section("SECTION 4: Seed reproducibility")

r1 = compile_and_run_c("pow(x,3)", "1000000 4 0 1 12345")
r2 = compile_and_run_c("pow(x,3)", "1000000 4 0 1 12345")
r3 = compile_and_run_c("pow(x,3)", "1000000 4 0 1 54321")

print(f"Same seed, run 1: {r1:.8f}")
print(f"Same seed, run 2: {r2:.8f}")
print(f"Different seed  : {r3:.8f}")

if r1 == r2:
    print("[PASS] identical seeds gave identical results")
    _pass_count += 1
else:
    print("[FAIL] identical seeds gave DIFFERENT results -- check RNG seeding per thread")
    _fail_count += 1

if r1 != r3:
    print("[PASS] different seeds gave different results")
    _pass_count += 1
else:
    print("[WARN] different seeds gave identical results (could be coincidence, "
          "but check that seed is actually being used)")


# =====================================================================
# SECTION 5: Range handling (negative, asymmetric, shifted ranges)
# =====================================================================

section("SECTION 5: Range handling")

check("x^2 on [-2,3] (= 35/3)", "pow(x,2)", lambda x: x**2,
      DEFAULT_N, DEFAULT_THREADS, -2, 3)

check("sin(x) on [-pi,pi] (~ 0)", "sin(x)", math.sin,
      DEFAULT_N, DEFAULT_THREADS, -math.pi, math.pi, tol=0.05)

check("exp(x) on [-5,0] (= 1-e^-5)", "exp(x)", math.exp,
      DEFAULT_N, DEFAULT_THREADS, -5, 0)

check("x^2 on tiny range [1,1.0001]", "pow(x,2)", lambda x: x**2,
      1_000_000, DEFAULT_THREADS, 1, 1.0001, tol=0.05,
      note="tiny interval -- sanity check for degenerate ranges")


# =====================================================================
# SECTION 6: Integrand min/max bound handling
# Only meaningful if your scheme uses the integrand bounds (e.g. a
# hit-or-miss / envelope method). Skip or delete this section if it
# doesn't apply to your algorithm.
# =====================================================================

section("SECTION 6: Integrand bound (min/max) handling")

# True bounds of sin(x) on [0, pi] are [0, 1] -- correct bounds given.
check("sin(x) on [0,pi] with correct bounds [min=0,max=1]",
      "sin(x)", math.sin, DEFAULT_N, DEFAULT_THREADS, 0, math.pi,
      imax=1, imin=0)

# Deliberately too-tight upper bound. If your algorithm relies on the
# stated max to build an envelope/bounding box, an incorrect (too low)
# bound should bias the result -- this is intentional, not a bug in the
# test. It's here to confirm the bound is actually being used/respected,
# and ideally that your program flags or handles an inconsistent bound
# rather than silently producing garbage.
print("\n-- intentionally WRONG bound below: expect a biased result, not a pass/fail --")
got_wrong = compile_and_run_c("sin(x)", f"{DEFAULT_N} {DEFAULT_THREADS} 0 {math.pi} 1 0.5 0")
print(f"sin(x) with WRONG max=0.5 (true max=1): got={got_wrong:.6f} "
      f"vs true={exact_sin:.6f}  (bias expected if bounds feed an envelope method)")

# Deliberately loose (safe but inefficient) bounds -- should NOT bias
# the result, just possibly cost some efficiency.
check("sin(x) on [0,pi] with LOOSE safe bounds [min=-1,max=2]",
      "sin(x)", math.sin, DEFAULT_N, DEFAULT_THREADS, 0, math.pi,
      imax=2, imin=-1, tol=0.03,
      note="loose bounds should stay unbiased, just less efficient")


# =====================================================================
# SECTION 7: Harder integrands (oscillation, sharp peaks, quick decay)
# =====================================================================

section("SECTION 7: Harder integrands")

check("sin(50*x) rapid oscillation on [0,1]", "sin(50*x)",
      lambda x: math.sin(50 * x), 20_000_000, 8, 0, 1, tol=0.08)

check("x^20 sharply peaked near x=1 on [0,1] (= 1/21)", "pow(x,20)",
      lambda x: x**20, 10_000_000, 8, 0, 1, tol=0.05)

check("exp(-x*x) gaussian-like on [-3,3]", "exp(-x*x)",
      lambda x: math.exp(-x * x), 10_000_000, 8, -3, 3, tol=0.03)

check("1/sqrt(x) integrable singularity at 0 on [0,1] (= 2)",
      "1/sqrt(x)", lambda x: 1 / math.sqrt(x) if x > 0 else 0,
      10_000_000, 8, 1e-9, 1, tol=0.1,
      note="near-singular endpoint, watch for x=0 evaluation issues")


# =====================================================================
# SECTION 8: Statistical variance sanity check
# Run the *same* problem many times with different seeds. The spread of
# results should be consistent with Monte Carlo statistics, and the
# average over trials should land very close to the true value.
# =====================================================================

section("SECTION 8: Statistical variance sanity check")

trials = 30
N_stat = 200_000
a_stat, b_stat = 0, 1
py_f = lambda x: x**2
exact_stat = simpsons_rule(py_f, a_stat, b_stat)

samples_out = []
for i in range(trials):
    try:
        r = compile_and_run_c("pow(x,2)", f"{N_stat} 4 {a_stat} {b_stat} {217483+i} 1 0")
        samples_out.append(r)
    except Exception as e:
        print(f"trial {i}: ERROR -> {e}")

if samples_out:
    mean = sum(samples_out) / len(samples_out)
    var = sum((s - mean) ** 2 for s in samples_out) / max(len(samples_out) - 1, 1)
    std = var ** 0.5

    # Crude-Monte-Carlo variance estimate: Var[avg f] = Var[f]/N, times (b-a)^2
    Area = (b_stat - a_stat) * (1 - 0)
    p = exact_stat / Area          # fraction of the bounding box under the curve
    theoretical_se = Area * math.sqrt(p * (1 - p) / N_stat)

    print(f"Trials: {len(samples_out)}, N per trial: {N_stat}")
    print(f"Empirical mean : {mean:.6f}  (exact: {exact_stat:.6f}, "
          f"diff {abs(mean-exact_stat):.6f})")
    print(f"Empirical std  : {std:.6f}")
    print(f"Theoretical SE: {theoretical_se:.6f}")
    print("Sanity checks: empirical mean should be within a few empirical std of "
          "the exact value, and empirical std should be within ~2-3x of the "
          "theoretical SE (order of magnitude, not exact match).")


# =====================================================================
# Summary
# =====================================================================

section("SUMMARY")
print(f"PASS:  {_pass_count}")
print(f"FAIL:  {_fail_count}")
print(f"ERROR: {_error_count}")
print("(Sections 3, 6's wrong-bound case, and 8 are diagnostic/exploratory "
      "and not counted as strict pass/fail.)")