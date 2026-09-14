# Quantum Key Distribution in the Post-Quantum Transition

### What security is physical, and what remains computational

**Robert Gardner · September 2026**  
School of Physics and Astronomy, University of Birmingham

**[Read the full paper (PDF)](docs/quantum-key-distribution.pdf)** · **[Explore the Python companion](bb84.py)** · **[Validation runs and generated figures](https://github.com/Robert-Study/Quantum-Distribution/actions/workflows/validate.yml)**

---

Quantum computing changes which cryptographic assumptions can be trusted. Quantum key distribution offers a way to establish shared secrets using the behaviour of quantum states, but turning that principle into a secure system requires much more than detecting an eavesdropper.

This review follows that gap from the BB84 protocol to real optical hardware, then considers where QKD fits alongside post-quantum cryptography. The Python companion makes the central probability arguments and engineering constraints reproducible.

> **Central argument:** QKD can bound an adversary's information under an explicit physical model. Authentication, device behaviour, optical loss and the wider communication protocol remain part of the security problem.

## At a glance

| Result | Meaning | Scope |
|---|---|---|
| **50%** basis-sifting efficiency | About half the detected signals survive when Alice and Bob choose their bases independently and uniformly. | Ideal, unbiased BB84. |
| **25%** QBER under full intercept–resend | Eve's random-basis measurement introduces errors into the sifted key. | One specific attack; not a universal detection threshold. |
| **≈11%** zero of the secret-fraction bound | The benchmark $1-2h_2(Q)$ becomes zero. | Asymptotic single-photon BB84 with symmetric bit/phase errors and ideal one-way processing. |
| **1%** fibre transmission at 100 km | A 0.2 dB/km channel loses 99% of the optical signal over 100 km. | Fibre attenuation alone; not a secret-key rate. |

**Contents:** [Threat model](#1-what-quantum-computing-changes) · [BB84](#2-how-bb84-establishes-correlations) · [Eavesdropping](#3-deriving-the-interceptresend-error-rate) · [Secrecy](#4-from-disturbance-to-a-secret-key) · [Hardware](#5-where-the-ideal-model-meets-hardware) · [QKD and PQC](#6-qkd-and-post-quantum-cryptography) · [Python](#7-reproduce-the-analysis-in-python) · [References](#references)

## 1. What quantum computing changes

RSA, Diffie–Hellman and elliptic-curve cryptography depend on the practical difficulty of factorisation or discrete logarithms. Shor's algorithm solves these problem classes in polynomial time on a sufficiently capable quantum computer. This threatens public-key operations used for key establishment and digital signatures.

Symmetric cryptography faces a different scaling change. Grover's algorithm reduces ideal exhaustive key-search complexity from $O(2^k)$ to $O(2^{k/2})$. That is a quadratic speed-up, and the cost of implementing the quantum computation still matters.

The distinction is important for migration. Increasing a symmetric key length and replacing a vulnerable public-key construction address different problems. Long-lived confidential information also creates a timing risk: an adversary can collect encrypted traffic today and attempt to decrypt it later.

The paper develops these comparisons as statements about algorithms and assumptions, rather than predictions of a particular date when existing encryption will fail. See references [3] and [4] in the [full paper](docs/quantum-key-distribution.pdf).

## 2. How BB84 establishes correlations

Alice prepares each bit in one of two mutually unbiased bases:

$$
\mathcal{B}_Z=\{\lvert0\rangle,\lvert1\rangle\},
\qquad
\mathcal{B}_X=\{\lvert+\rangle,\lvert-\rangle\},
\qquad
\lvert\pm\rangle=\frac{\lvert0\rangle\pm\lvert1\rangle}{\sqrt{2}}.
$$

| Bit | Basis | State | Example polarisation |
|---|---|---|---|
| 0 | $Z$ | $\lvert0\rangle$ | Horizontal |
| 1 | $Z$ | $\lvert1\rangle$ | Vertical |
| 0 | $X$ | $\lvert+\rangle$ | +45° |
| 1 | $X$ | $\lvert-\rangle$ | −45° |

Bob chooses a measurement basis independently. A matching basis recovers Alice's bit in the ideal model; a complementary basis gives a uniformly random outcome.

After transmission, they announce their bases over an **authenticated classical channel**, keeping only matching-basis events. With unbiased choices,

$$
P_{\mathrm{sift}}=P(ZZ)+P(XX)=\frac14+\frac14=\frac12.
$$

These sifted bits are not yet a final secret key. Alice and Bob must estimate channel errors, reconcile their bit strings and apply privacy amplification. Authentication prevents an adversary from substituting two independent sessions for their intended conversation.

## 3. Deriving the intercept–resend error rate

Suppose Eve intercepts every signal, measures in a randomly selected basis and sends Bob a replacement state corresponding to her outcome.

Condition on a **sifted event**, so Alice and Bob used the same basis.

| Eve's basis | Probability | Bob's conditional error probability | Contribution to QBER |
|---|---:|---:|---:|
| Matches Alice's | $1/2$ | $0$ | $0$ |
| Differs from Alice's | $1/2$ | $1/2$ | $1/4$ |

Therefore,

$$
Q_{\mathrm{IR}}
=\frac12(0)+\frac12\left(\frac12\right)
=\frac14.
$$

This **25% error rate is conditional on basis sifting**. Dividing errors by all transmitted signals would calculate a different quantity.

The Python companion extends the example to an intercepted fraction $f$. With otherwise ideal measurements,

$$
Q(f)=\frac{f}{4}.
$$

It also permits an independent classical bit-flip probability $e$ on Bob's result:

$$
Q(f,e)=e+\frac{f}{4}(1-2e).
$$

The second expression accounts for the possibility that two flips cancel. It is an illustrative noise model, not a model of every physical error source. Likewise, a QBER measurement alone cannot identify which attack or hardware imperfection produced it.

## 4. From disturbance to a secret key

An error signature illustrates the physics; it does not constitute a security proof.

The binary entropy function is

$$
h_2(x)=-x\log_2x-(1-x)\log_2(1-x),
\qquad h_2(0)=h_2(1)=0.
$$

For the ideal asymptotic single-photon model, with equal bit and phase error rates and ideal one-way post-processing, a secret fraction per sifted bit is bounded by

$$
r\geq 1-2h_2(Q).
$$

One entropy term represents the cost of error reconciliation; the other accounts for privacy amplification. Solving $h_2(Q)=1/2$ gives

$$
Q_{\mathrm{th}}\approx0.110028.
$$

A negative right-hand side certifies no positive secret fraction through this bound. It does not mean that a negative number of key bits exists. The companion exports both the signed bound and its nonnegative benchmark.

This approximately 11% value belongs to a particular security model. It is not a universal operating limit for QKD, and substituting a finite simulation's measured QBER into the expression does not establish finite-key security. See the [Shor–Preskill proof](https://arxiv.org/abs/quant-ph/0003004).

### What “secure” means

A useful key must be both correct and secret: Alice and Bob should agree, and their key should be close to uniform and independent of Eve.

For an abort-capable protocol, an acceptance-aware secrecy statement takes the form

$$
\frac{p_{\mathrm{pass}}}{2}
\left\|
\rho_{K_AE\mid\mathrm{pass}}
-\tau_{K_A}\otimes\rho_{E\mid\mathrm{pass}}
\right\|_1
\leq\varepsilon_{\mathrm{sec}}.
$$

Here $p_{\mathrm{pass}}$ is the acceptance probability and $\tau_{K_A}$ is an ideal uniform key state. Correctness bounds the probability that the protocol accepts unequal keys. Together, the correctness and secrecy errors determine the composable security parameter.

The acceptance factor matters when distinguishing an overall protocol guarantee from a guarantee conditioned on a potentially rare successful run. See [Portmann and Renner](https://arxiv.org/abs/2102.00021) for the formal framework.

## 5. Where the ideal model meets hardware

### Weak coherent pulses and decoy states

Practical transmitters often use attenuated laser pulses. For a phase-randomised coherent pulse with mean photon number $\mu$,

$$
P_\mu(n)=e^{-\mu}\frac{\mu^n}{n!},
\qquad
P_\mu(n\geq2)=1-(1+\mu)e^{-\mu}.
$$

At $\mu=0.5$, approximately **9.0% of emitted pulses contain multiple photons**. This is a source statistic, not a fraction of secret bits or a direct measure of information leakage.

Multiphoton signals introduce a vulnerability absent from an ideal single-qubit model: an adversary may retain a photon and delay measurement until the basis is announced. Decoy-state methods vary pulse intensity to constrain the single-photon contribution using observed detection statistics.

The paper includes the asymptotic decoy-state expression

$$
R\geq q\left[-Q_\mu f_{\mathrm{EC}}h_2(E_\mu)
+Q_1\bigl(1-h_2(e_1)\bigr)\right].
$$

Here $R$ is per emitted pulse, $q$ is the sifting factor, $Q_\mu$ is the signal gain, $E_\mu$ is its QBER, $f_{\mathrm{EC}}$ represents error-correction inefficiency, and $Q_1,e_1$ describe the single-photon contribution. **This rate is distinct from the per-sifted-bit fraction above.** The companion plots source probabilities; it does not estimate decoy-state yields or calculate a secure decoy-state rate.

### Optical attenuation

With attenuation coefficient $\alpha$ in dB/km and length $L$ in km,

$$
\eta_{\mathrm{ch}}(L)=10^{-\alpha L/10}.
$$

For the paper's illustrative $\alpha=0.2$ dB/km:

| Distance | Fibre loss | Transmittance |
|---:|---:|---:|
| 50 km | 10 dB | $10^{-1}$ |
| 100 km | 20 dB | $10^{-2}$ |
| 200 km | 40 dB | $10^{-4}$ |
| 500 km | 100 dB | $10^{-10}$ |

These calculations exclude detector inefficiency, coupling losses and background counts. They explain why long-distance fibre demonstrations require careful engineering, but they cannot predict an installation's key throughput.

### Devices, authentication and availability

Source leakage, detector side channels and characterisation errors can invalidate the correspondence between an implementation and its proof. Measurement-device-independent QKD moves measurement attacks into the adversarial model; it still requires assumptions about other parts of the system.

QKD also requires authenticated classical communication. It does not secure compromised endpoints or prevent an adversary from blocking the optical channel. An abort may preserve secrecy while leaving the service unavailable.

The [full paper](docs/quantum-key-distribution.pdf) discusses these constraints, satellite links, long-distance fibre experiments and the role of alternative architectures in more detail.

## 6. QKD and post-quantum cryptography

| Question | QKD | Post-quantum cryptography |
|---|---|---|
| What does it provide? | Shared key material through a quantum protocol. | Key establishment and signatures through classical algorithms. |
| What supports security? | Quantum constraints under a stated device and protocol model. | Computational assumptions believed to resist classical and quantum attacks. |
| What infrastructure is needed? | Suitable optical links, transmitters and detectors. | Conventional processors and digital networks, with migration work. |
| How is identity established? | An authenticated classical channel is required separately. | Appropriate signature and authenticated protocol constructions can provide it. |
| What constrains deployment? | Optical loss, hardware cost, trust boundaries and topology. | Integration, performance, cryptographic agility and implementation assurance. |

NIST's 2024 standards distinguish these cryptographic tasks:

- **[FIPS 203 / ML-KEM](https://csrc.nist.gov/pubs/fips/203/final):** a key-encapsulation mechanism.
- **[FIPS 204 / ML-DSA](https://csrc.nist.gov/pubs/fips/204/final):** lattice-based digital signatures.
- **[FIPS 205 / SLH-DSA](https://csrc.nist.gov/pubs/fips/205/final):** hash-based digital signatures.

The review's engineering judgement is that PQC offers the broadly deployable migration path, while QKD may justify dedicated infrastructure on selected links. Hybrid designs can combine different security assumptions, but concatenating two secrets is not by itself a complete protocol: the combiner, authentication and failure handling need their own analysis.

## 7. Reproduce the analysis in Python

The companion is a small, readable **classical simulation of quantum measurement probabilities**. It samples Alice's preparation, Eve's optional measurement and resend, Bob's measurement, and basis sifting. It requires no quantum SDK or quantum hardware.

### Run

Use **Python 3.11 or later**. The simulation, numerical calculations and tests use the standard library.

~~~bash
python bb84.py --pulses 100000 --seed 42
~~~

To generate the four-panel figure:

~~~bash
python -m pip install -r requirements.txt
python bb84.py --pulses 100000 --seed 42 --plot
~~~

Explore independent channel noise or increase the sample size:

~~~bash
python bb84.py --pulses 200000 --noise 0.02 --seed 42 --plot --output results/noisy
~~~

Each run sweeps interception from 0% to 100% in 10% increments. Sweep point $i$ uses seed $42+i$ when the base seed is 42. Identical inputs are reproducible within the same Python environment; small sample differences across environments should be assessed statistically.

### Outputs

| File in the chosen output directory | Contents |
|---|---|
| <code>intercept-sweep.csv</code> | Measured QBER, analytical expectation, sifted counts and approximate 95% Wilson intervals. |
| <code>secret-fraction.csv</code> | The signed $1-2h_2(Q)$ bound and a nonnegative benchmark. |
| <code>fibre-loss.csv</code> | Fibre-only transmission over 0–500 km. |
| <code>photon-statistics.csv</code> | Vacuum, single-photon and multiphoton probabilities. |
| <code>summary.json</code> | Parameters, seeds, model assumptions, threshold and endpoint simulation results. |
| <code>bb84-benchmarks.png</code> / <code>.svg</code> | Four-panel figure, when <code>--plot</code> is supplied. |

**Expected analytical behaviour:** without noise, no interception produces zero sifted errors; full interception approaches 25% QBER; basis agreement approaches 50%. These are expectations, not invented experimental measurements.

The figure compares interception errors against the analytical prediction, plots the signed secret-fraction bound, uses a logarithmic axis for fibre transmission, and shows the coherent-pulse photon probabilities.

### Checks

~~~bash
python -m unittest discover -s tests -v
~~~

Tests check entropy endpoints and the numerical threshold, known fibre-loss values, photon probabilities, input validation, reproducibility and simulated error rates against independent analytical expectations. GitHub Actions runs the tests and figure generation, then retains the resulting CSVs, figures and software versions as a downloadable <code>bb84-results</code> artifact for 30 days.

### Model limits

This code was added as a numerical companion to the review. It is not the source of experimental data in the paper, and it does not implement a deployable QKD system.

- Seeded pseudorandom sampling is for reproducibility, not cryptographic key generation.
- The interception simulation assumes ideal detected single photons. Fibre attenuation and coherent-pulse statistics are separate calculations.
- Authentication, parameter-estimation sampling, error correction, privacy amplification, finite-key proofs and general quantum attacks are not implemented.
- Wilson intervals describe sampling uncertainty in this simulation. They are not composable secrecy bounds.
- A QBER or a positive asymptotic benchmark alone does not certify a secure key.

## References

The [original paper](docs/quantum-key-distribution.pdf) contains the complete bibliography of 20 sources. Key starting points are:

1. C. H. Bennett and G. Brassard, *Quantum Cryptography: Public Key Distribution and Coin Tossing* (1984). Foundational BB84 protocol; reference [5] in the paper.
2. P. W. Shor and J. Preskill, [*Simple Proof of Security of the BB84 Quantum Key Distribution Protocol*](https://arxiv.org/abs/quant-ph/0003004), Physical Review Letters **85**, 441–444 (2000).
3. V. Scarani et al., [*The Security of Practical Quantum Key Distribution*](https://doi.org/10.1103/RevModPhys.81.1301), Reviews of Modern Physics **81**, 1301–1350 (2009).
4. C. Portmann and R. Renner, [*Security in Quantum Cryptography*](https://arxiv.org/abs/2102.00021), Reviews of Modern Physics **94**, 025008 (2022).
5. NIST, [FIPS 203](https://csrc.nist.gov/pubs/fips/203/final), [FIPS 204](https://csrc.nist.gov/pubs/fips/204/final) and [FIPS 205](https://csrc.nist.gov/pubs/fips/205/final) (2024).

---

**Document note:** the PDF is preserved as supplied. This README is an adapted reading guide with a new Python companion, an explicit acceptance-aware secrecy formulation, and additional numerical examples. No new experimental data are claimed.
