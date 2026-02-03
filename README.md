# QGIS-Kernel-Raster-Filter
A QGIS plugin to apply custom convolution filters (kernels) to raster
layers.

*Features* :

-> Supports any square kernel (3x3, 5x5, etc.) loaded from a text file.

-> Processes all raster bands automatically.

-> Uses scipy and GDAL for efficient convolution.

*Usage* :

1- Load a raster layer.

2- Go to Raster > Kernel Raster Filter > Run Kernel Filter.

3- Select your raster and a .txt file containing the kernel values.

4- Run the algorithm.

*Kernel File Format* :

-> Values separated by spaces or commas. 

  Example (Sharpen) :

0 -1 0

\-1 5 -1

0 -1 0
