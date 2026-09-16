import unittest
import importlib.util
from pathlib import Path

from qgis.core import QgsCoordinateReferenceSystem


PLUGIN_DIR = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location('latlontools_util', PLUGIN_DIR / 'util.py')
UTIL = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(UTIL)


class ParseCoordinateStringTest(unittest.TestCase):

    def test_dms_in_non_wgs84_geographic_crs(self):
        crs = QgsCoordinateReferenceSystem('EPSG:4674')

        y, x = UTIL.parseCoordinateString(
            '10\N{DEGREE SIGN} 09\' 37.166" S, '
            '056\N{DEGREE SIGN} 07\' 25.893" W',
            crs,
            order=0,
        )

        self.assertAlmostEqual(y, -10.16032388888889)
        self.assertAlmostEqual(x, -56.12385916666667)

    def test_decimal_degrees_in_geographic_crs(self):
        crs = QgsCoordinateReferenceSystem('EPSG:4674')

        y, x = UTIL.parseCoordinateString(
            '-10.16032388888889, -56.12385916666667', crs, order=0
        )

        self.assertAlmostEqual(y, -10.16032388888889)
        self.assertAlmostEqual(x, -56.12385916666667)

    def test_decimal_degrees_in_geographic_crs_xy_order(self):
        crs = QgsCoordinateReferenceSystem('EPSG:4674')

        y, x = UTIL.parseCoordinateString(
            '-56.12385916666667, -10.16032388888889', crs, order=1
        )

        self.assertAlmostEqual(y, -10.16032388888889)
        self.assertAlmostEqual(x, -56.12385916666667)

    def test_numeric_coordinates_in_projected_crs_yx_order(self):
        crs = QgsCoordinateReferenceSystem('EPSG:31981')

        y, x = UTIL.parseCoordinateString(
            '8876731.994, 595977.189', crs, order=0
        )

        self.assertAlmostEqual(y, 8876731.994)
        self.assertAlmostEqual(x, 595977.189)

    def test_numeric_coordinates_in_projected_crs_xy_order(self):
        crs = QgsCoordinateReferenceSystem('EPSG:31981')

        y, x = UTIL.parseCoordinateString(
            '595977.189, 8876731.994', crs, order=1
        )

        self.assertAlmostEqual(y, 8876731.994)
        self.assertAlmostEqual(x, 595977.189)

    def test_dms_is_rejected_for_projected_crs(self):
        crs = QgsCoordinateReferenceSystem('EPSG:31981')

        with self.assertRaises(ValueError):
            UTIL.parseCoordinateString(
                '10\N{DEGREE SIGN} 09\' 37.166" S, '
                '056\N{DEGREE SIGN} 07\' 25.893" W',
                crs,
                order=0,
            )


if __name__ == '__main__':
    unittest.main()
