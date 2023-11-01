from PyQt5.QtWidgets import QWidget, QVBoxLayout
import pyqtgraph as pg


class GraphingWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.layout = QVBoxLayout()

        self.setWindowTitle("Lensors - graphing")

        self.graphWidget = pg.PlotWidget(axisItems={"bottom": pg.DateAxisItem()})
        self.graphWidget.addLegend()
        self.graphWidget.setBackground("w")

        self.layout.addWidget(self.graphWidget)
        self.setLayout(self.layout)
