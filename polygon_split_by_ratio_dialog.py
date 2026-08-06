from qgis.PyQt.QtWidgets import (
    QDialog, QVBoxLayout, QFormLayout, QLineEdit, QDialogButtonBox, QLabel
)
from qgis.gui import QgsMapLayerComboBox
from qgis.core import QgsMapLayerProxyModel


class PolygonSplitByRatioDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Poligon felosztasa arany szerint")
        self.resize(420, 220)

        layout = QVBoxLayout(self)

        info = QLabel(
            "Valaszd ki a felosztando poligon reteget, egy vonal reteget "
            "(a vagovonalak ezzel lesznek parhuzamosak), majd add meg az "
            "aranyokat vesszovel elvalasztva (pl. 3,2,1)."
        )
        info.setWordWrap(True)
        layout.addWidget(info)

        form = QFormLayout()

        self.polygonCombo = QgsMapLayerComboBox()
        self.polygonCombo.setFilters(QgsMapLayerProxyModel.PolygonLayer)
        form.addRow("Felosztando poligon reteg:", self.polygonCombo)

        self.lineCombo = QgsMapLayerComboBox()
        self.lineCombo.setFilters(QgsMapLayerProxyModel.LineLayer)
        form.addRow("Irany (vonal) reteg:", self.lineCombo)

        self.ratiosEdit = QLineEdit()
        self.ratiosEdit.setPlaceholderText("pl. 3,2,1")
        form.addRow("Felosztasi aranyok:", self.ratiosEdit)

        layout.addLayout(form)

        self.buttonBox = QDialogButtonBox(
            QDialogButtonBox.Ok | QDialogButtonBox.Cancel
        )
        self.buttonBox.accepted.connect(self.accept)
        self.buttonBox.rejected.connect(self.reject)
        layout.addWidget(self.buttonBox)

    def getPolygonLayer(self):
        return self.polygonCombo.currentLayer()

    def getLineLayer(self):
        return self.lineCombo.currentLayer()

    def getRatios(self):
        text = self.ratiosEdit.text().strip()
        if not text:
            return None
        try:
            values = [float(x.strip()) for x in text.split(",") if x.strip() != ""]
        except ValueError:
            return None
        if len(values) < 2 or any(v <= 0 for v in values):
            return None
        return values
