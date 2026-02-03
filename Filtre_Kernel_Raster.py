import os
from qgis.PyQt.QtCore import QCoreApplication, QFileInfo
from qgis.PyQt.QtGui import QIcon
from qgis.PyQt.QtWidgets import QAction
from qgis.core import (QgsProcessingProvider, 
                       QgsApplication,
                       QgsRasterLayer)
from qgis import processing
from .FiltreKernelRasterAlgorithm import KernelRasterFilterAlgorithm

class KernelRasterFilterProvider(QgsProcessingProvider):
    def loadAlgorithms(self, *args):
        self.addAlgorithm(KernelRasterFilterAlgorithm())

    def id(self):
        return 'kernel_filters'

    def name(self):
        return 'Kernel Filters'

    def icon(self):
        return QIcon(":/images/themes/default/processingToolbox.svg")

class KernelRasterFilterPlugin:
    def __init__(self, iface):
        self.iface = iface
        self.provider = None
        self.action = None
        
    def initProcessing(self):
        self.provider = KernelRasterFilterProvider()
        QgsApplication.processingRegistry().addProvider(self.provider)

    def initGui(self):
        self.initProcessing()
        
        # Load icon
        plugin_dir = os.path.dirname(__file__)
        icon_path = os.path.join(plugin_dir, 'icon.png')
        
        if not os.path.exists(icon_path):
            self.action = QAction(QIcon(":/images/themes/default/processingAlgorithm.svg"), "Run Kernel Filter", self.iface.mainWindow())
        else:
            self.action = QAction(QIcon(icon_path), "Run Kernel Filter", self.iface.mainWindow())
            
        self.action.triggered.connect(self.run)
        self.action.setStatusTip("Apply a convolution kernel filter to the active raster layer")
        
        # Add to Menu
        self.iface.addPluginToRasterMenu("Kernel Raster Filter", self.action)

        # Add to Toolbar
        raster_toolbar = self.iface.rasterToolBar()
        if raster_toolbar:
            raster_toolbar.addAction(self.action)

    def unload(self):
        QgsApplication.processingRegistry().removeProvider(self.provider)
        self.iface.removePluginRasterMenu("Kernel Raster Filter", self.action)
        
        raster_toolbar = self.iface.rasterToolBar()
        if raster_toolbar and self.action:
            raster_toolbar.removeAction(self.action)
            
        del self.action

    def run(self):
        active_layer = self.iface.activeLayer()
        initial_params = {}
        if active_layer and isinstance(active_layer, QgsRasterLayer):
            initial_params['INPUT_RASTER'] = active_layer
        processing.execAlgorithmDialog("kernel_filters:kernelrasterfilter", initial_params)