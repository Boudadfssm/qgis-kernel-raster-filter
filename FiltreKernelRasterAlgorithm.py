from qgis.PyQt.QtCore import QCoreApplication
from qgis.core import (QgsProcessing, 
                      QgsProcessingAlgorithm, 
                      QgsProcessingParameterRasterLayer,
                      QgsProcessingParameterFile,
                      QgsProcessingParameterRasterDestination,
                      QgsProcessingException)
from qgis.PyQt.QtGui import QIcon
import numpy as np
from osgeo import gdal
from scipy.ndimage import convolve
import os
import traceback
import math

class KernelRasterFilterAlgorithm(QgsProcessingAlgorithm):
    INPUT_RASTER = 'INPUT_RASTER'
    KERNEL_FILE = 'KERNEL_FILE'
    OUTPUT_RASTER = 'OUTPUT_RASTER'

    def tr(self, string):
        return QCoreApplication.translate('KernelRasterFilter', string)

    def createInstance(self):
        return KernelRasterFilterAlgorithm()

    def name(self):
        return 'kernelrasterfilter'

    def displayName(self):
        return self.tr(' Raster Kernel Filter')

    def group(self):
        return self.tr('Convolution')

    def groupId(self):
        return 'convolution'

    def shortHelpString(self) -> str:
        return self.tr(
            "<b>Applies a custom convolution filter to all raster bands.</b><br>"
            "The kernel file (.txt) must contain values separated by spaces or commas.<br>"
            "Example for a 3x3 sharpen filter:<br>"
            "0 -1 0<br>-1 5 -1<br>0 -1 0"
        )

    def icon(self):
        plugin_dir = os.path.dirname(__file__)
        icon_path = os.path.join(plugin_dir, 'icon.png')
        return QIcon(icon_path)

    def initAlgorithm(self, config=None):
        self.addParameter(QgsProcessingParameterRasterLayer(self.INPUT_RASTER, self.tr('📁 Input Raster')))
        self.addParameter(QgsProcessingParameterFile(self.KERNEL_FILE, self.tr('📄 Kernel File (.txt)'), fileFilter='Text Files (*.txt *.TXT)'))
        self.addParameter(QgsProcessingParameterRasterDestination(self.OUTPUT_RASTER, self.tr('💾 Filtered Raster')))

    def processAlgorithm(self, parameters, context, feedback):
        raster_layer = self.parameterAsRasterLayer(parameters, self.INPUT_RASTER, context)
        kernel_file = self.parameterAsString(parameters, self.KERNEL_FILE, context)
        output_path = self.parameterAsOutputLayer(parameters, self.OUTPUT_RASTER, context)

        if not raster_layer: 
            raise QgsProcessingException(self.tr('No raster layer selected.'))
            
        raster_path = raster_layer.source()
        feedback.pushInfo(f'🔄 Raster: {raster_layer.name()}')

        if not os.path.exists(raster_path): 
            raise QgsProcessingException(self.tr('Source raster file not found on disk.'))
        if not os.path.exists(kernel_file): 
            raise QgsProcessingException(self.tr('Kernel file not found.'))

        # --- READ KERNEL ---
        kernel = None
        try:
            with open(kernel_file, 'r', encoding='utf-8') as f:
                content = f.read()
                content = content.replace(',', ' ')
                values = [float(x) for x in content.split() if x.strip()]
            
            if not values:
                raise ValueError("File is empty or contains no valid numbers.")

            count = len(values)
            root = math.isqrt(count)
            if root * root != count:
                raise QgsProcessingException(
                    self.tr(f'Kernel must be square (e.g., 3x3=9, 5x5=25). Found {count} values.')
                )
            
            kernel = np.array(values).reshape((root, root))
            feedback.pushInfo(f'✅ Kernel loaded: {root}x{root}')

        except Exception as e:
            raise QgsProcessingException(self.tr(f'Error reading kernel file: {str(e)}'))

        # --- PROCESSING ---
        try:
            ds = gdal.Open(raster_path)
            if ds is None: 
                raise QgsProcessingException(self.tr('GDAL opening error'))
            
            band_count = ds.RasterCount
            cols, rows = ds.RasterXSize, ds.RasterYSize
            gt = ds.GetGeoTransform()
            proj = ds.GetProjection()
            
            feedback.pushInfo(f'📊 Dimensions: {cols}x{rows}, Bands: {band_count}')

            driver = gdal.GetDriverByName('GTiff')
            out_ds = driver.Create(output_path, cols, rows, band_count, gdal.GDT_Float32)
            out_ds.SetGeoTransform(gt)
            out_ds.SetProjection(proj)

            total_steps = band_count
            current_step = 0

            for i in range(1, band_count + 1):
                if feedback.isCanceled():
                    break

                current_step += 1
                feedback.setProgress(int(current_step / total_steps * 100))
                feedback.pushInfo(f'⚙️ Processing band {i}/{band_count}...')
                
                band = ds.GetRasterBand(i)
                data = band.ReadAsArray()
                nodata = band.GetNoDataValue()
                
                result = convolve(data.astype(np.float64), kernel, mode='reflect')
                
                if nodata is not None:
                    result[data == nodata] = nodata

                out_band = out_ds.GetRasterBand(i)
                out_band.WriteArray(result)
                out_band.SetRasterColorInterpretation(band.GetRasterColorInterpretation())
                if nodata is not None:
                    out_band.SetNoDataValue(float(nodata))
            
            out_ds.FlushCache()
            out_ds = None
            ds = None
            
            if not feedback.isCanceled():
                feedback.pushInfo('✅ Finished successfully!')
            
        except Exception as e:
            feedback.reportError(self.tr(f'Processing error: {str(e)}'))
            feedback.pushDebugInfo(traceback.format_exc())
            return {}

        return {self.OUTPUT_RASTER: output_path}