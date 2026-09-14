"""Reproduce ideal BB84 benchmarks from the accompanying QKD review.

This is a classical Monte Carlo model of BB84 measurement statistics.
It does not implement a secure key exchange or generate application keys.
"""
from __future__ import annotations

import argparse
import csv
import json
import math
import random
from dataclasses import asdict, dataclass
from pathlib import Path


def probability(value: float, name: str = "probability", maximum: float = 1.0) -> float:
    if not math.isfinite(value) or not 0.0 <= value <= maximum:
        raise ValueError(f"{name} must be finite and in [0, {maximum}]")
    return value


def binary_entropy(p: float) -> float:
    """Binary entropy in bits, with the continuous endpoint values."""
    probability(p)
    if p in (0.0, 1.0):
        return 0.0
    return -p * math.log2(p) - (1.0 - p) * math.log2(1.0 - p)


def secret_fraction_bound(qber: float) -> float:
    """Signed 1 - 2h2(Q) benchmark; a negative bound certifies no key.

    Assumes asymptotic single-photon BB84, symmetric bit/phase errors,
    and ideal one-way error correction. This is not a finite-key estimate.
    """
    probability(qber, "QBER", maximum=0.5)
    return 1.0 - 2.0 * binary_entropy(qber)


def key_threshold() -> float:
    """Solve h2(Q) = 1/2 on [0, 1/2] by bisection."""
    low, high = 0.0, 0.5
    for _ in range(60):
        mid = (low + high) / 2.0
        if secret_fraction_bound(mid) > 0.0:
            low = mid
        else:
            high = mid
    return (low + high) / 2.0


def fibre_transmittance(distance_km: float, attenuation_db_per_km: float = 0.2) -> float:
    """Fibre-only transmission; excludes detector/coupling losses and noise."""
    for name, value in (("distance", distance_km), ("attenuation", attenuation_db_per_km)):
        if not math.isfinite(value) or value < 0.0:
            raise ValueError(f"{name} must be finite and non-negative")
    return 10.0 ** (-attenuation_db_per_km * distance_km / 10.0)


def photon_probabilities(mu: float) -> tuple[float, float, float]:
    """P(0), P(1), P(n >= 2) for a phase-randomised coherent pulse."""
    if not math.isfinite(mu) or mu < 0.0:
        raise ValueError("mean photon number must be finite and non-negative")
    p0 = math.exp(-mu)
    p1 = mu * p0
    # For small mu, avoid cancellation in 1 - (1 + mu) exp(-mu).
    if mu < 1e-3:
        p_multi = mu * mu * (0.5 + mu * (-1.0 / 3.0 + mu * (1.0 / 8.0 - mu / 30.0)))
    else:
        p_multi = -math.expm1(-mu) - p1
    return p0, p1, max(0.0, p_multi)


def expected_qber(intercept_fraction: float, noise: float = 0.0) -> float:
    """Independent intercept-resend errors followed by a classical bit flip."""
    probability(intercept_fraction, "intercept fraction")
    probability(noise, "noise", maximum=0.5)
    attack_error = intercept_fraction / 4.0
    return noise + attack_error * (1.0 - 2.0 * noise)


def wilson_interval(errors: int, total: int) -> tuple[float, float]:
    """Approximate 95% binomial interval, not a QKD secrecy bound."""
    if not isinstance(total, int) or not isinstance(errors, int) or total < 1 or not 0 <= errors <= total:
        raise ValueError("counts must be integers with 0 <= errors <= total and total > 0")
    z = 1.959963984540054
    observed = errors / total
    denominator = 1.0 + z * z / total
    centre = (observed + z * z / (2.0 * total)) / denominator
    half = z * math.sqrt(observed * (1.0 - observed) / total + z * z / (4.0 * total**2)) / denominator
    return max(0.0, centre - half), min(1.0, centre + half)


@dataclass(frozen=True)
class Simulation:
    pulses: int
    intercept_fraction: float
    noise: float
    seed: int
    intercepted: int
    sifted: int
    errors: int

    @property
    def qber(self) -> float | None:
        return self.errors / self.sifted if self.sifted else None

    def row(self) -> dict:
        result = asdict(self)
        low, high = wilson_interval(self.errors, self.sifted) if self.sifted else (None, None)
        result.update(
            sift_fraction=self.sifted / self.pulses,
            qber=self.qber,
            qber_ci_low=low,
            qber_ci_high=high,
            expected_qber=expected_qber(self.intercept_fraction, self.noise),
        )
        return result


def simulate(pulses: int = 100_000, intercept_fraction: float = 1.0,
             noise: float = 0.0, seed: int = 42) -> Simulation:
    """Sample preparation, Eve's measurement/resend, Bob's measurement, and sifting.

    Basis 0 is Z; basis 1 is X. Wrong-basis measurements are uniformly random.
    Each trial uses an ideal detected single photon; optical loss is modelled
    separately by fibre_transmittance(), not folded into this experiment.
    """
    if isinstance(pulses, bool) or not isinstance(pulses, int) or pulses < 1:
        raise ValueError("pulses must be a positive integer")
    probability(intercept_fraction, "intercept fraction")
    probability(noise, "noise", maximum=0.5)
    rng = random.Random(seed)  # Reproducibility only; not cryptographic randomness.
    intercepted = sifted = errors = 0
    for _ in range(pulses):
        alice_bit, alice_basis, bob_basis = (rng.randrange(2) for _ in range(3))
        transmitted_bit, transmitted_basis = alice_bit, alice_basis
        if rng.random() < intercept_fraction:
            intercepted += 1
            eve_basis = rng.randrange(2)
            transmitted_bit = alice_bit if eve_basis == alice_basis else rng.randrange(2)
            transmitted_basis = eve_basis
        bob_bit = transmitted_bit if bob_basis == transmitted_basis else rng.randrange(2)
        if rng.random() < noise:
            bob_bit ^= 1
        if alice_basis == bob_basis:
            sifted += 1
            errors += int(alice_bit != bob_bit)
    return Simulation(pulses, intercept_fraction, noise, seed, intercepted, sifted, errors)


def write_csv(path: Path, rows: list[dict]) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def make_plot(output: Path, sweep: list[dict], entropy_rows: list[dict],
              fibre_rows: list[dict], photon_rows: list[dict]) -> None:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    plt.rcParams.update({"font.size": 10, "axes.spines.top": False, "axes.spines.right": False})
    figure, axes = plt.subplots(2, 2, figsize=(11, 8), constrained_layout=True)
    navy, teal, orange = "#17324d", "#138a88", "#d78128"

    axis = axes[0, 0]
    measured = [r for r in sweep if r["qber"] is not None]
    x = [100 * r["intercept_fraction"] for r in measured]
    y = [100 * r["qber"] for r in measured]
    errors = [
        [100 * max(0.0, r["qber"] - r["qber_ci_low"]) for r in measured],
        [100 * max(0.0, r["qber_ci_high"] - r["qber"]) for r in measured],
    ]
    axis.plot([100 * r["intercept_fraction"] for r in sweep],
              [100 * r["expected_qber"] for r in sweep], color=navy, label="Analytical expectation")
    axis.errorbar(x, y, yerr=errors, fmt="o", capsize=3, color=teal, label="Simulation / 95% Wilson interval")
    axis.set(title="A  Interception and sifted-key errors", xlabel="Signals intercepted (%)", ylabel="QBER (%)")
    axis.legend(fontsize=8)

    axis = axes[0, 1]
    axis.plot([100 * r["qber"] for r in entropy_rows],
              [r["signed_bound"] for r in entropy_rows], color=navy)
    axis.axhline(0, color="grey", linewidth=0.8)
    axis.axvline(100 * key_threshold(), color=orange, linestyle="--",
                 label=f"Zero at {100 * key_threshold():.2f}%")
    axis.set(title="B  Ideal asymptotic benchmark", xlabel="QBER (%)", ylabel="1 - 2h2(Q), per sifted bit")
    axis.legend(fontsize=8)

    axis = axes[1, 0]
    axis.semilogy([r["distance_km"] for r in fibre_rows],
                  [r["transmittance"] for r in fibre_rows], color=teal)
    axis.set(title="C  Fibre attenuation only (0.2 dB/km)", xlabel="Fibre length (km)", ylabel="Channel transmittance")

    axis = axes[1, 1]
    for key, label, colour in (("p_zero", "Vacuum", navy), ("p_one", "Single photon", teal),
                               ("p_multi", "Two or more photons", orange)):
        axis.plot([r["mu"] for r in photon_rows], [r[key] for r in photon_rows],
                  label=label, color=colour)
    axis.set(title="D  Phase-randomised coherent pulses", xlabel="Mean photon number", ylabel="Probability")
    axis.legend(fontsize=8)
    for axis in axes.flat:
        axis.grid(alpha=0.15)
    figure.suptitle("BB84: connecting the probability model to engineering limits", fontsize=15, weight="bold")
    figure.savefig(output / "bb84-benchmarks.png", dpi=180)
    figure.savefig(output / "bb84-benchmarks.svg")
    plt.close(figure)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--pulses", type=int, default=100_000, help="ideal signals per sweep point")
    parser.add_argument("--seed", type=int, default=42, help="seed for reproducible simulation")
    parser.add_argument("--noise", type=float, default=0.0, help="independent Bob bit-flip probability, 0 to 0.5")
    parser.add_argument("--output", type=Path, default=Path("results"))
    parser.add_argument("--plot", action="store_true", help="also render figures (requires matplotlib)")
    args = parser.parse_args()
    if args.pulses < 1:
        parser.error("--pulses must be positive")
    try:
        probability(args.noise, "noise", maximum=0.5)
    except ValueError as error:
        parser.error(str(error))
    if args.plot:
        try:
            import matplotlib  # noqa: F401
        except ImportError:
            parser.error("--plot requires: python -m pip install -r requirements.txt")

    sweep = [simulate(args.pulses, i / 10, args.noise, args.seed + i).row() for i in range(11)]
    entropy_rows = [
        {"qber": i / 1000, "signed_bound": secret_fraction_bound(i / 1000),
         "nonnegative_benchmark": max(0.0, secret_fraction_bound(i / 1000))}
        for i in range(161)
    ]
    fibre_rows = [{"distance_km": length, "attenuation_db_per_km": 0.2,
                   "transmittance": fibre_transmittance(length)} for length in range(501)]
    photon_rows = []
    for i in range(201):
        p0, p1, pmulti = photon_probabilities(i / 100)
        photon_rows.append({"mu": i / 100, "p_zero": p0, "p_one": p1, "p_multi": pmulti})

    args.output.mkdir(parents=True, exist_ok=True)
    for filename, rows in (("intercept-sweep.csv", sweep), ("secret-fraction.csv", entropy_rows),
                            ("fibre-loss.csv", fibre_rows), ("photon-statistics.csv", photon_rows)):
        write_csv(args.output / filename, rows)
    summary = {
        "model": "Ideal BB84 measurement statistics; not a secure key exchange",
        "pulses_per_sweep_point": args.pulses, "base_seed": args.seed, "noise": args.noise,
        "seed_rule": "base_seed + sweep index",
        "ideal_asymptotic_qber_threshold": key_threshold(),
        "no_interception": sweep[0], "full_interception": sweep[-1],
        "assumptions": [
            "Independent unbiased Z/X basis choices and ideal single-photon measurements",
            "Classical seeded pseudorandom sampling, not quantum hardware",
            "Optical loss and photon statistics are separate analytical calculations",
            "No authentication, parameter-estimation sacrifice, error correction, or privacy amplification",
            "Wilson intervals are sampling summaries, not finite-key secrecy guarantees",
        ],
    }
    (args.output / "summary.json").write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    if args.plot:
        make_plot(args.output, sweep, entropy_rows, fibre_rows, photon_rows)
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
