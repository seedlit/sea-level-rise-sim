# TODO: account for areas below mean sea level
# TODO: account for areas that are already at new sea level
# TODO: add feature to give area incresed by sea level rise
# TODO: replace gdal's polygonization by grass's polygonization
# TODO: some post-processing

import numpy as np
import gdal
import os
import osr, ogr, gdal
import geopandas as gpd
import geoplot as gplt

# import matlplotlib.pyplot as plt
from matplotlib import pyplot as plt
from multiprocessing import Pool


def edit_dem_wrt_sea_level(dem_path, sea_level):
    dem_array = gdal.Open(dem_path).ReadAsArray()
    # dem_array[dem_array <= sea_level] = sea_level
    dem_array[(np.where((dem_array <= sea_level) & (dem_array != 0)))] = sea_level
    dem_array[dem_array > sea_level] = 0
    return dem_array


def save_array_as_geotif(array, source_tif_path, out_path):
    """
    Generates a geotiff raster from the input numpy array (height * width * depth)
    Input:
        array: {numpy array} numpy array to be saved as geotiff
        source_tif_path: {string} path to the geotiff from which projection and geotransformation information will be extracted.
    Output:
        out_path: {string} path to the generated Geotiff raster
    """
    if len(array.shape) > 2:
        height, width, depth = array.shape
    else:
        height, width = array.shape
        depth = 1
    source_tif = gdal.Open(source_tif_path)
    driver = gdal.GetDriverByName("GTiff")
    dataset = driver.Create(out_path, width, height, depth, gdal.GDT_Float32)
    if depth != 1:
        for i in range(depth):
            dataset.GetRasterBand(i + 1).WriteArray(array[:, :, i])
    else:
        dataset.GetRasterBand(1).WriteArray(array)
    geotrans = source_tif.GetGeoTransform()
    proj = source_tif.GetProjection()
    dataset.SetGeoTransform(geotrans)
    dataset.SetProjection(proj)
    dataset.FlushCache()
    dataset = None


def polygonize_raster(img_path, out_path):
    try:
        sourceRaster = gdal.Open(img_path)
        band = sourceRaster.GetRasterBand(1)
        driver = ogr.GetDriverByName("ESRI Shapefile")
        outShp = out_path
        # If shapefile already exist, delete it
        if os.path.exists(outShp):
            driver.DeleteDataSource(outShp)
        outDatasource = driver.CreateDataSource(outShp)
        # get proj from raster
        srs = osr.SpatialReference()
        srs.ImportFromWkt(sourceRaster.GetProjectionRef())
        # create layer with proj
        outLayer = outDatasource.CreateLayer(outShp, srs)
        # Add class column (0,255) to shapefile
        newField = ogr.FieldDefn("DN", ogr.OFTInteger)
        outLayer.CreateField(newField)
        gdal.Polygonize(band, None, outLayer, 0, [], callback=None)
        outDatasource.Destroy()
        sourceRaster = None
    except Exception as e:
        print("gdal Polygonize Error: " + str(e))


def remove_background(shp_path, remove_DN_value=0):
    ds = ogr.Open(shp_path, update=True)  # True allows to edit the shapefile
    lyr = ds.GetLayer()
    i = 0
    for _ in lyr:
        # if _["DN"] == remove_DN_value:
        if _["value"] == remove_DN_value:
            lyr.DeleteFeature(i)
        i += 1
    ds.Destroy()


def plot_poly_vector_file(vector_path):
    vector = gpd.read_file(vector_path)
    gplt.polyplot(vector)
    plt.show()


def raster_to_vector(raster, vector, temp_variable):
    cmd = (
        'grass -c {}  {}_MyMap --exec bash -c "r.import input={} output=prediction; r.to.vect input=prediction output=polygon type=area; '
        'v.out.ogr input=polygon output={} format="ESRI_Shapefile" --overwrite"'.format(
            raster, temp_variable, raster, vector
        )
    )
    rmdir = "rm -r ./{}_MyMap".format(temp_variable)
    os.system(cmd)
    os.system(rmdir)


def generate_flooded_shp(dem_path, sea_level_rise, out_dir):
    os.makedirs(out_dir, exist_ok=True)
    out_dem_path = os.path.join(
        out_dir, "flooded_dem_{}cm.tif".format(int(sea_level_rise * 100))
    )
    out_shp_path = os.path.join(
        out_dir, "flooded_shp_{}cm.shp".format(int(sea_level_rise * 100))
    )
    edited_dem_array = edit_dem_wrt_sea_level(dem_path, sea_level_rise)
    save_array_as_geotif(edited_dem_array, dem_path, out_dem_path)
    from time import time

    start_time = time()
    # polygonize_raster(out_dem_path, out_shp_path)
    raster_to_vector(out_dem_path, out_shp_path, int(sea_level_rise * 100))
    print("polygonization took {} seconds".format(time() - start_time))
    remove_background(out_shp_path, 0)


if __name__ == "__main__":

    dem_path = ""
    out_dir = ""
    num_processes = 2
    start_sea_level_cm = 0
    end_sea_level_cm = 5000
    step_size_cm = 100

    task_list = []
    for i in range(start_sea_level_cm, end_sea_level_cm + step_size_cm, step_size_cm):
        task_list.append([dem_path, i / 100, out_dir])
    print("Files for total {} sea rise levels will be generated".format(len(task_list)))
    p = Pool(num_processes)
    p.starmap(generate_flooded_shp, task_list)
    p.close()
    p.join()
