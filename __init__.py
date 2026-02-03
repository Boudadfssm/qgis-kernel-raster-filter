def classFactory(iface):
    from .Filtre_Kernel_Raster import KernelRasterFilterPlugin
    return KernelRasterFilterPlugin(iface)