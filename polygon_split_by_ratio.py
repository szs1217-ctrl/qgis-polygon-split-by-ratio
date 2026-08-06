import os
import math

from qgis.PyQt.QtWidgets import QAction, QMessageBox
from qgis.PyQt.QtGui import QIcon
from qgis.PyQt.QtCore import QVariant
from qgis.core import (
    QgsGeometry, QgsPointXY, QgsField, QgsVectorLayer,
    QgsProject, QgsFeature, QgsCoordinateTransform
)

from .polygon_split_by_ratio_dialog import PolygonSplitByRatioDialog


class PolygonSplitByRatio:
    def __init__(self, iface):
        self.iface = iface
        self.actions = []
        self.menu = "Poligon felosztas arany szerint"
        self.dlg = None

    def initGui(self):
        icon_path = os.path.join(os.path.dirname(__file__), "icon.png")
        icon = QIcon(icon_path) if os.path.exists(icon_path) else QIcon()
        self.action = QAction(icon, "Poligon felosztas arany szerint...", self.iface.mainWindow())
        self.action.triggered.connect(self.run)
        self.iface.addPluginToMenu(self.menu, self.action)
        self.iface.addToolBarIcon(self.action)
        self.actions.append(self.action)

    def unload(self):
        for action in self.actions:
            self.iface.removePluginMenu(self.menu, action)
            self.iface.removeToolBarIcon(action)

    def run(self):
        self.dlg = PolygonSplitByRatioDialog(self.iface.mainWindow())
        if not self.dlg.exec_():
            return

        polygon_layer = self.dlg.getPolygonLayer()
        line_layer = self.dlg.getLineLayer()
        ratios = self.dlg.getRatios()

        if polygon_layer is None or line_layer is None:
            QMessageBox.warning(
                self.iface.mainWindow(), "Hiba",
                "Valassz ki egy poligon es egy vonal reteget!"
            )
            return

        if ratios is None:
            QMessageBox.warning(
                self.iface.mainWindow(), "Hiba",
                "Adj meg legalabb ket, vesszovel elvalasztott pozitiv szamot "
                "az aranyokhoz (pl. 3,2,1)!"
            )
            return

        poly_feat = self._get_single_feature(polygon_layer, "poligon")
        if poly_feat is None:
            return

        line_feat = self._get_single_feature(line_layer, "vonal")
        if line_feat is None:
            return

        line_geometry = line_feat.geometry()
        if line_layer.crs() != polygon_layer.crs():
            transform = QgsCoordinateTransform(
                line_layer.crs(), polygon_layer.crs(), QgsProject.instance()
            )
            line_geometry = QgsGeometry(line_geometry)
            line_geometry.transform(transform)

        try:
            result_geoms = self.split_polygon(
                poly_feat.geometry(), line_geometry, ratios
            )
        except Exception as e:
            QMessageBox.critical(
                self.iface.mainWindow(), "Hiba a feldolgozas soran", str(e)
            )
            return

        crs = polygon_layer.crs().authid()
        out = QgsVectorLayer(f"Polygon?crs={crs}", "felosztott_reszek", "memory")
        prov = out.dataProvider()
        prov.addAttributes([
            QgsField("resz_sorszam", QVariant.Int),
            QgsField("arany", QVariant.Double),
            QgsField("terulet", QVariant.Double),
        ])
        out.updateFields()

        for i, (g, a) in enumerate(zip(result_geoms, ratios), start=1):
            f = QgsFeature()
            f.setGeometry(g)
            f.setAttributes([i, a, g.area()])
            prov.addFeature(f)

        QgsProject.instance().addMapLayer(out)
        QMessageBox.information(
            self.iface.mainWindow(), "Kesz",
            f"A poligon {len(ratios)} reszre lett felosztva."
        )

    def _get_single_feature(self, layer, label):
        feats = list(layer.selectedFeatures())
        if feats:
            if len(feats) > 1:
                QMessageBox.warning(
                    self.iface.mainWindow(), "Hiba",
                    f"Tobb {label} van kijelolve - jelolj ki pontosan egyet, "
                    f"vagy torold a kijelolest, ha a reteg csak egy elemet tartalmaz!"
                )
                return None
            return feats[0]

        feats = list(layer.getFeatures())
        if len(feats) != 1:
            QMessageBox.warning(
                self.iface.mainWindow(), "Hiba",
                f"Jelolj ki pontosan egy {label}t a megfelelo retegen (vagy "
                f"a retegnek csak egy eleme legyen)!"
            )
            return None
        return feats[0]

    @staticmethod
    def split_polygon(geom, line_geom, ratios):
        geom = QgsGeometry(geom)

        if line_geom.isMultipart():
            parts = line_geom.asMultiPolyline()
            if not parts:
                raise ValueError("A vonal geometriaja ures.")
            line_pts = parts[0]
        else:
            line_pts = line_geom.asPolyline()

        if len(line_pts) < 2:
            raise ValueError("A vonalnak legalabb 2 pontbol kell allnia.")

        p0, p1 = line_pts[0], line_pts[-1]
        dx, dy = p1.x() - p0.x(), p1.y() - p0.y()
        if dx == 0 and dy == 0:
            raise ValueError("A vonal ket vegpontja megegyezik, nem hatarozza meg az iranyt.")

        angle_deg = math.degrees(math.atan2(dy, dx))
        center = p0

        geom_rot = QgsGeometry(geom)
        geom_rot.rotate(angle_deg, center)

        if geom_rot.isEmpty():
            raise ValueError("A poligon geometriaja ervenytelen vagy ures.")

        bbox = geom_rot.boundingBox()
        total_area = geom_rot.area()
        if total_area <= 0:
            raise ValueError("A kivalasztott poligon terulete nulla vagy ervenytelen.")

        ratio_sum = sum(ratios)
        target_areas = [total_area * r / ratio_sum for r in ratios]

        y0, y1 = bbox.yMinimum(), bbox.yMaximum()
        x0, x1 = bbox.xMinimum() - 1, bbox.xMaximum() + 1

        def strip_geom(a, b):
            pts = [
                QgsPointXY(x0, a), QgsPointXY(x1, a),
                QgsPointXY(x1, b), QgsPointXY(x0, b), QgsPointXY(x0, a)
            ]
            return QgsGeometry.fromPolygonXY([pts])

        def find_cut(start, target_area, upper):
            lo_, hi_ = start, upper
            for _ in range(60):
                mid = (lo_ + hi_) / 2
                part = geom_rot.intersection(strip_geom(start, mid))
                if part.area() < target_area:
                    lo_ = mid
                else:
                    hi_ = mid
            return (lo_ + hi_) / 2

        parts_rot = []
        current = y0
        for target in target_areas[:-1]:
            cut = find_cut(current, target, y1)
            parts_rot.append(geom_rot.intersection(strip_geom(current, cut)))
            current = cut
        parts_rot.append(geom_rot.intersection(strip_geom(current, y1)))

        result = []
        for r in parts_rot:
            r2 = QgsGeometry(r)
            r2.rotate(-angle_deg, center)
            result.append(r2)

        return result
