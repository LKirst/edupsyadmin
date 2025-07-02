import unittest

from edupsyadmin.core.convert_measures import (
    iq_to_t,
    iq_to_z,
    normaldist_to_z,
    percentile_to_t,
    percentile_to_z,
    t_to_z,
    z_to_normaldist,
)


class TestConversionFunctions(unittest.TestCase):
    def test_percentile_to_z(self):
        self.assertAlmostEqual(percentile_to_z(50), 0, places=5)
        self.assertAlmostEqual(percentile_to_z(84), 0.994, places=3)
        self.assertAlmostEqual(percentile_to_z(97), 1.881, places=3)

    def test_percentile_to_t(self):
        self.assertAlmostEqual(percentile_to_t(50), 50, places=5)
        self.assertAlmostEqual(percentile_to_t(84), 59.9, places=1)
        self.assertAlmostEqual(percentile_to_t(97), 68.8, places=1)

    def test_z_to_normaldist(self):
        self.assertAlmostEqual(z_to_normaldist(0, 50, 10), 50)
        self.assertAlmostEqual(z_to_normaldist(1, 50, 10), 60)
        self.assertAlmostEqual(z_to_normaldist(-1, 50, 10), 40)

    def test_normaldist_to_z(self):
        self.assertAlmostEqual(normaldist_to_z(50, 50, 10), 0)
        self.assertAlmostEqual(normaldist_to_z(60, 50, 10), 1)
        self.assertAlmostEqual(normaldist_to_z(40, 50, 10), -1)

    def test_iq_to_z(self):
        self.assertAlmostEqual(iq_to_z(100), 0)
        self.assertAlmostEqual(iq_to_z(115), 1)
        self.assertAlmostEqual(iq_to_z(85), -1)

    def test_t_to_z(self):
        self.assertAlmostEqual(t_to_z(50), 0)
        self.assertAlmostEqual(t_to_z(60), 1)
        self.assertAlmostEqual(t_to_z(40), -1)

    def test_iq_to_t(self):
        self.assertAlmostEqual(iq_to_t(100), 50)
        self.assertAlmostEqual(iq_to_t(115), 60)
        self.assertAlmostEqual(iq_to_t(85), 40)


if __name__ == "__main__":
    unittest.main()
