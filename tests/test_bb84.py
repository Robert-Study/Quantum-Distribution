"""Analytical and statistical checks for the educational BB84 model."""
import math
import unittest

from bb84 import (
    Simulation, binary_entropy, expected_qber, fibre_transmittance,
    key_threshold, photon_probabilities, secret_fraction_bound,
    simulate, wilson_interval,
)


class BB84Tests(unittest.TestCase):
    def test_error_free_channel_and_sifting(self):
        result = simulate(40_000, intercept_fraction=0, seed=101)
        self.assertEqual(result.errors, 0)
        self.assertEqual(result.intercepted, 0)
        self.assertLess(abs(result.sifted - result.pulses / 2),
                        6 * math.sqrt(result.pulses / 4))

    def test_intercept_resend_matches_analytical_expectation(self):
        for fraction, noise in ((0.4, 0.0), (1.0, 0.0), (0.0, 0.05), (0.8, 0.03)):
            with self.subTest(fraction=fraction, noise=noise):
                result = simulate(60_000, fraction, noise, seed=2026)
                # Independently derived probability of one, but not both,
                # of an interception error and an independent channel flip.
                p = fraction / 4 * (1 - noise) + (1 - fraction / 4) * noise
                sigma = math.sqrt(p * (1 - p) / result.sifted)
                self.assertLess(abs(result.qber - p), 6 * sigma)

    def test_reproducibility(self):
        self.assertEqual(simulate(500, 0.5, seed=12), simulate(500, 0.5, seed=12))

    def test_entropy_and_threshold(self):
        self.assertEqual(binary_entropy(0), 0)
        self.assertEqual(binary_entropy(1), 0)
        self.assertEqual(binary_entropy(0.5), 1)
        self.assertEqual(secret_fraction_bound(0), 1)
        self.assertEqual(secret_fraction_bound(0.5), -1)
        self.assertAlmostEqual(key_threshold(), 0.11002786443835955, places=12)
        self.assertGreater(secret_fraction_bound(0.10), 0)
        self.assertLess(secret_fraction_bound(0.12), 0)

    def test_fibre_reference_values(self):
        for length, expected in ((0, 1), (50, 0.1), (100, 0.01), (200, 1e-4), (500, 1e-10)):
            with self.subTest(length=length):
                self.assertAlmostEqual(fibre_transmittance(length) / expected, 1, places=12)
        self.assertEqual(fibre_transmittance(100, 0), 1)

    def test_photon_statistics(self):
        self.assertEqual(photon_probabilities(0), (1, 0, 0))
        for mu in (1e-10, 1e-5, 0.1, 0.5, 1.0, 10):
            p0, p1, pmulti = photon_probabilities(mu)
            self.assertAlmostEqual(p0 + p1 + pmulti, 1, places=14)
            self.assertTrue(all(0 <= value <= 1 for value in (p0, p1, pmulti)))
        self.assertAlmostEqual(photon_probabilities(0.5)[2], 0.09020401043104986, places=12)
        self.assertAlmostEqual(photon_probabilities(1e-10)[2] / 1e-20, 0.5, places=9)

    def test_sampling_intervals_and_empty_sift(self):
        low, high = wilson_interval(0, 100)
        self.assertAlmostEqual(low, 0)
        self.assertGreater(high, 0)
        low, high = wilson_interval(100, 100)
        self.assertLess(low, 1)
        self.assertAlmostEqual(high, 1)
        empty = Simulation(1, 0, 0, 42, 0, 0, 0)
        self.assertIsNone(empty.qber)
        self.assertIsNone(empty.row()["qber_ci_low"])

    def test_invalid_inputs(self):
        calls = [
            lambda: simulate(0), lambda: simulate(True), lambda: simulate(2.5),
            lambda: simulate(10, intercept_fraction=1.1),
            lambda: simulate(10, noise=0.6),
            lambda: simulate(10, noise=float("nan")),
            lambda: secret_fraction_bound(-0.1),
            lambda: secret_fraction_bound(0.6),
            lambda: binary_entropy(float("inf")),
            lambda: fibre_transmittance(-1),
            lambda: fibre_transmittance(5, -0.1),
            lambda: photon_probabilities(-1),
            lambda: photon_probabilities(float("nan")),
            lambda: wilson_interval(0, 0),
            lambda: wilson_interval(11, 10),
            lambda: expected_qber(-1),
        ]
        for call in calls:
            with self.assertRaises(ValueError):
                call()


if __name__ == "__main__":
    unittest.main()
