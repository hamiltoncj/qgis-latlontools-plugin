import importlib
import os
from pathlib import Path
from types import ModuleType, SimpleNamespace
import sys
import unittest


os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')

from qgis.core import (  # noqa: E402
    QgsApplication,
    QgsCoordinateReferenceSystem,
    QgsVectorDataProvider,
)


PLUGIN_DIR = Path(__file__).resolve().parents[1]
PACKAGE_NAME = 'latlontools_test'
PACKAGE = ModuleType(PACKAGE_NAME)
PACKAGE.__path__ = [str(PLUGIN_DIR)]
sys.modules[PACKAGE_NAME] = PACKAGE

QGIS_APP = QgsApplication([], False)
QGIS_APP.initQgis()

ZOOM_MODULE = importlib.import_module(f'{PACKAGE_NAME}.zoomToLatLon')
DIGITIZER_MODULE = importlib.import_module(f'{PACKAGE_NAME}.digitizer')


class FakeSettings:

    def __init__(self, mode, crs, order=0):
        self.mode = mode
        self.crs = crs
        self.zoomToCoordOrder = order

    def __getattr__(self, name):
        if name.startswith('zoomToProjIs'):
            selected = {
                'zoomToProjIsWgs84': 'wgs84',
                'zoomToProjIsProjectCRS': 'project',
            }.get(name)
            return lambda: selected == self.mode
        raise AttributeError(name)

    def zoomToCustomCRS(self):
        return self.crs


class FakeCanvas:

    def __init__(self, crs):
        self.crs = crs

    def mapSettings(self):
        return self

    def destinationCrs(self):
        return self.crs


class FakeLineEdit:

    def __init__(self, value):
        self.value = value
        self.cleared = False

    def text(self):
        return self.value

    def clear(self):
        self.cleared = True


class FakeLayer:

    def __init__(self, crs):
        self._crs = crs

    def dataProvider(self):
        return self

    def capabilities(self):
        return QgsVectorDataProvider.Capability.AddFeatures

    def crs(self):
        return self._crs


class FakeVectorLayerTools:

    def __init__(self):
        self.geometry = None

    def addFeature(self, layer, attributes, geometry):
        self.geometry = geometry
        return True, None


class FakeMessageBar:

    def __init__(self):
        self.messages = []

    def pushMessage(self, *args, **kwargs):
        self.messages.append((args, kwargs))


class FakeInterface:

    def __init__(self, layer):
        self.layer = layer
        self.layer_tools = FakeVectorLayerTools()
        self.message_bar = FakeMessageBar()

    def activeLayer(self):
        return self.layer

    def vectorLayerTools(self):
        return self.layer_tools

    def messageBar(self):
        return self.message_bar


class FakeLatLonTools:

    def __init__(self):
        self.zoom = None

    def zoomTo(self, crs, y, x):
        self.zoom = crs, y, x


class GeographicCrsInputTest(unittest.TestCase):

    def setUp(self):
        self.crs = QgsCoordinateReferenceSystem('EPSG:4674')
        self.coordinate = (
            '10\N{DEGREE SIGN} 09\' 37.166" S, '
            '056\N{DEGREE SIGN} 07\' 25.893" W'
        )

    def test_zoom_accepts_dms_in_project_geographic_crs(self):
        subject = SimpleNamespace(
            settings=FakeSettings('project', self.crs),
            canvas=FakeCanvas(self.crs),
        )

        y, x, bounds, source_crs = ZOOM_MODULE.ZoomToLatLon.convertCoordinate(
            subject, self.coordinate
        )

        self.assertAlmostEqual(y, -10.16032388888889)
        self.assertAlmostEqual(x, -56.12385916666667)
        self.assertIsNone(bounds)
        self.assertEqual(source_crs.authid(), 'EPSG:4674')

    def test_digitizer_adds_dms_point_in_project_geographic_crs(self):
        layer = FakeLayer(self.crs)
        iface = FakeInterface(layer)
        line_edit = FakeLineEdit(self.coordinate)
        lltools = FakeLatLonTools()
        subject = SimpleNamespace(
            inputProjection=2,
            inputXYOrder=0,
            canvas=FakeCanvas(self.crs),
            iface=iface,
            lineEdit=line_edit,
            lltools=lltools,
        )

        DIGITIZER_MODULE.DigitizerWidget.addFeature(subject)

        point = iface.layer_tools.geometry.asPoint()
        self.assertAlmostEqual(point.y(), -10.16032388888889)
        self.assertAlmostEqual(point.x(), -56.12385916666667)
        self.assertTrue(line_edit.cleared)
        self.assertEqual(iface.message_bar.messages, [])
        self.assertEqual(lltools.zoom[0].authid(), 'EPSG:4674')


if __name__ == '__main__':
    unittest.main()
