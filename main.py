import os
import gdal
from multiprocessing import Pool
from sea_level_rise import generate_flooded_shp
from generate_flood_screenshot import save_screenshot, generate_gif


def get_bounds_from_raster(raster_path):
    # TODO: ensure that crs of raster is 4326
    raster = gdal.Open(raster_path)
    x_size = raster.RasterXSize
    y_size = raster.RasterYSize
    geotrans = raster.GetGeoTransform()
    left = geotrans[0]
    top = geotrans[3]
    right = geotrans[0] + (geotrans[1] * x_size)
    bottom = geotrans[3] + (geotrans[4] * y_size)
    return left, bottom, right, top


if __name__ == "__main__":

    # define inputs ---------------------------------------
    dem_path = "/home/naman/Desktop/side_projects/world_sea_level_rise/data/dems/global/india_90m/india_merged_360m_clipped.tif"
    out_dir = (
        "/home/naman/Desktop/side_projects/world_sea_level_rise/india_batch_outputs"
    )
    num_processes = 2
    start_sea_level_cm = 0
    end_sea_level_cm = 5000
    step_size_cm = 100
    gif_image_duration = 0.15
    target_epsg = 4326

    # this part generates the flooded tifs and shapfiles
    print("Generating the flooded DEMs and shapfiles")
    flooded_files_out_dir = os.path.join(out_dir, "flooded_tifs_and_shps")
    os.makedirs(flooded_files_out_dir, exist_ok=True)
    task_list = []
    for i in range(start_sea_level_cm, end_sea_level_cm + step_size_cm, step_size_cm):
        task_list.append([dem_path, i / 100, flooded_files_out_dir])
    print("Files for total {} sea rise levels will be generated".format(len(task_list)))
    p = Pool(num_processes)
    p.starmap(generate_flooded_shp, task_list)
    p.close()
    p.join()

    # this part generates screenshots --------------------------------------------
    print("Generating screenshots")
    screenshots_dir = os.path.join(out_dir, "screenshots")
    os.makedirs(screenshots_dir, exist_ok=True)
    left, bottom, right, top = get_bounds_from_raster(dem_path)
    task_list = []
    for shp in os.listdir(flooded_files_out_dir):
        if shp.endswith(".shp"):
            shp_path = os.path.join(flooded_files_out_dir, shp)
            shp_name = shp_path.split("/")[-1].split(".")[0]
            out_img_path = os.path.join(screenshots_dir, "{}.png".format(shp_name))
            task_list.append(
                [bottom, left, top, right, target_epsg, shp_path, out_img_path]
            )
    print("total {} screenshots will be generated".format(len(task_list)))
    p = Pool(num_processes)
    p.starmap(save_screenshot, task_list)
    p.close()
    p.join()

    # this part generates the gif using generated screenshots -----------------------
    print("Generating GIF")
    generate_gif(
        screenshots_dir, os.path.join(out_dir, "sea_level_rise.gif"), gif_image_duration
    )
    print("FINISHED!")
