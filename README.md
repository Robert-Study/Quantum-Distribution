# Quantum Key Distribution in the Post-Quantum Transition

*What security is physical, and what remains computational*

Robert Gardner · September 2026  
School of Physics and Astronomy, University of Birmingham

[Paper (PDF)](docs/quantum-key-distribution.pdf) · [Python code](bb84.py) · [Tests](https://github.com/Robert-Study/Quantum-Distribution/actions/workflows/validate.yml)

Quantum key distribution is often described as “unhackable encryption”. That description misses two things: QKD establishes keys, and its security depends on how closely the equipment matches the assumptions in the proof.

This paper uses BB84 to examine those assumptions. It starts with the disturbance caused by an intercept–resend attack, works through the ideal secret-key bound, then considers weak laser pulses, detector behaviour and optical loss. The final section compares QKD with post-quantum cryptography and discusses where dedicated quantum links might be justified.

The Python script explores the same calculations. It simulates BB84 measurements and lets you vary the fraction of intercepted signals and the background error rate.

## BB84 and the cost of interception

Alice encodes a random bit in either the $Z$ basis or the $X$ basis:

$$
\mathcal{B}_Z=\{\lvert0\rangle,\lvert1\rangle\},
\qquad
\mathcal{B}_X=\{\lvert+\rangle,\lvert-\rangle\},
\qquad
\lvert\pm\rangle=\frac{\lvert0\rangle\pm\lvert1\rangle}{\sqrt{2}}.
$$

Bob independently chooses a measurement basis. After transmission, they compare bases over an authenticated classical channel and discard the mismatches. With unbiased choices, about half the detected signals survive this sifting step.

Suppose Eve intercepts every signal, measures in a random basis and resends the resulting state. On sifted events, she chooses the wrong basis half the time. When she does, Bob's result has a 50% chance of disagreeing with Alice's bit. The resulting quantum bit error rate is

$$
Q_{\mathrm{IR}}=\frac12\times\frac12=\frac14.
$$

The denominator here is the number of **sifted signals**, not the number transmitted.

For an intercepted fraction $f$, the expected QBER is $f/4$. The script also allows an independent bit-flip probability $e$ on Bob's result:

$$
Q(f,e)=e+\frac{f}{4}(1-2e).
$$

The factor $1-2e$ accounts for two flips cancelling. This simple model is useful for checking the simulation, although real attacks and hardware errors can produce different statistics.

## How much key can be retained?

For asymptotic single-photon BB84 with symmetric bit and phase error rates and ideal one-way post-processing, the secret fraction per sifted bit satisfies

$$
r\geq1-2h_2(Q),
\qquad
h_2(Q)=-Q\log_2Q-(1-Q)\log_2(1-Q).
$$

The bound reaches zero at $Q\approx0.110028$, or about 11%. A negative value means this expression cannot certify a positive key fraction. The script keeps the signed result as well as a version clipped at zero.

The 11% value depends on the assumptions above. It is not a general acceptance threshold for QKD. In particular, a finite simulation does not supply the error estimates or secrecy proof needed to establish a secure key. The [Shor–Preskill paper](https://arxiv.org/abs/quant-ph/0003004) gives the underlying argument.

The review also discusses correctness and composable secrecy. When a protocol can abort, the acceptance probability needs to be accounted for: an overall security bound is different from a bound conditioned on a rare successful run. [Portmann and Renner](https://arxiv.org/abs/2102.00021) give the formal treatment.

## Sources, detectors and distance

An attenuated laser does not emit exactly one photon per pulse. For a phase-randomised coherent pulse with mean photon number $\mu$,

$$
P_\mu(n)=e^{-\mu}\frac{\mu^n}{n!},
\qquad
P_\mu(n\geq2)=1-(1+\mu)e^{-\mu}.
$$

At $\mu=0.5$, about 9.0% of emitted pulses contain more than one photon. Eve may be able to keep one photon and wait for the basis announcement before measuring it. Decoy-state methods vary the pulse intensity to constrain the single-photon contribution from the observed detection statistics.

Fibre loss imposes a separate constraint. At attenuation $\alpha$ dB/km over a distance $L$ km,

$$
\eta_{\mathrm{ch}}=10^{-\alpha L/10}.
$$

Using the paper's example of 0.2 dB/km gives 1% transmission at 100 km, $10^{-4}$ at 200 km and $10^{-10}$ at 500 km. These figures include fibre attenuation only. Detector efficiency, coupling and background counts are needed before calculating a practical key rate.

The paper covers detector side channels, measurement-device-independent QKD and satellite links in more detail. The security proof has to describe the devices actually used; it cannot make a faulty implementation secure.

## QKD alongside post-quantum cryptography

Shor's algorithm threatens the factorisation and discrete-logarithm assumptions used by RSA, Diffie–Hellman and elliptic-curve systems. Grover's algorithm gives a quadratic speed-up for ideal exhaustive symmetric-key search. These are different migration problems.

Post-quantum cryptography addresses them on conventional computing and network infrastructure. NIST's 2024 standards include [ML-KEM for key establishment](https://csrc.nist.gov/pubs/fips/203/final), [ML-DSA](https://csrc.nist.gov/pubs/fips/204/final) and [SLH-DSA](https://csrc.nist.gov/pubs/fips/205/final) for signatures.

For most networks, PQC is the more practical migration route. QKD may add value on selected fixed links where the threat model warrants dedicated optical equipment. It still needs authentication and secure endpoints, and an attacker can disrupt the link. A hybrid scheme needs a suitable key combiner and clear failure handling; simply joining two secrets is not a complete design.

## Running the simulation

Use Python 3.11 or later. The calculations and tests use the standard library; Matplotlib is needed only for plots.

~~~bash
python bb84.py --pulses 100000 --seed 42
~~~

To generate the figures:

~~~bash
python -m pip install -r requirements.txt
python bb84.py --pulses 100000 --seed 42 --plot
~~~

For a run with 2% independent bit-flip noise:

~~~bash
python bb84.py --pulses 200000 --noise 0.02 --seed 42 --plot --output results/noisy
~~~

Each run sweeps interception from 0% to 100% in steps of 10%. The seed is incremented at each step. With the same inputs and Python environment, the run is repeatable.

Results are written to the selected output directory:

| File | Contents |
|---|---|
| <code>intercept-sweep.csv</code> | Sifted counts, errors, QBER and 95% Wilson intervals |
| <code>secret-fraction.csv</code> | Signed and clipped secret-fraction bounds |
| <code>fibre-loss.csv</code> | Transmission over 0–500 km |
| <code>photon-statistics.csv</code> | Vacuum, single-photon and multiphoton probabilities |
| <code>summary.json</code> | Run parameters, assumptions and summary results |
| <code>bb84-benchmarks.png</code> / <code>.svg</code> | Four plots, when <code>--plot</code> is used |

### Example results

A [Python 3.12 run](https://github.com/Robert-Study/Quantum-Distribution/actions/runs/34860618160) with 100,000 signals per step, base seed 42 and no added noise produced:

| Interception | Sifted signals | Errors | QBER | Expected |
|---|---:|---:|---:|---:|
| 0% | 50,334 | 0 | 0% | 0% |
| 100% | 49,896 | 12,508 | 25.07% | 25% |

The simulation recovers the expected error rate within sampling variation. The calculated zero of the secret-fraction bound is 0.1100278644.

### Tests and assumptions

~~~bash
python -m unittest discover -s tests -v
~~~

The tests cover the analytical limits, fibre-loss values, photon probabilities, reproducibility and simulated error rates. GitHub Actions also generates the plots and saves the outputs and software versions as a <code>bb84-results</code> artifact for 30 days.

This is a classical probability simulation of ideal, detected single photons. Optical loss and coherent-pulse statistics are calculated separately. It uses seeded pseudorandom numbers and omits authentication, parameter-estimation sampling, error correction and privacy amplification. The Wilson intervals describe sampling uncertainty, not finite-key security. The code is for studying the protocol and must not be used to generate cryptographic keys.

## References

The PDF contains the full bibliography. The main sources for the calculations are:

- C. H. Bennett and G. Brassard, *Quantum Cryptography: Public Key Distribution and Coin Tossing* (1984), reference [5] in the paper.
- P. W. Shor and J. Preskill, [*Simple Proof of Security of the BB84 Quantum Key Distribution Protocol*](https://arxiv.org/abs/quant-ph/0003004), Physical Review Letters **85**, 441–444 (2000).
- V. Scarani et al., [*The Security of Practical Quantum Key Distribution*](https://doi.org/10.1103/RevModPhys.81.1301), Reviews of Modern Physics **81**, 1301–1350 (2009).
- C. Portmann and R. Renner, [*Security in Quantum Cryptography*](https://arxiv.org/abs/2102.00021), Reviews of Modern Physics **94**, 025008 (2022).
