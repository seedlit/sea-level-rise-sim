# TODO: add text
# TODO: can also add image to basemap witg transparency
# TODO: Background methods - arcgisimage - highres - important
# TODO: can add rivers (map.drawrivers()) and also river flooding in next version
# TODO: can add wmsimage
# TODO: add map.colorbar to represent sea level rise values
# TODO: add drawmapscale
# TODO: from mpl_toolkits.basemap import interp - will be useful while handling DEM and RGB of different resolutions
# TODO: is_land will be useful while implementing will-you-drown?
# TODO: multiple subplots gif'
# TODO: inset plots gif will be useful when input will be a single lat-lon --> this point can be zoomed in inset
# TODO: add other basemaps like terrain, releif, etc. besides RGB
# TODO: Simplify shapefile

from mpl_toolkits.basemap import Basemap
import matplotlib.pyplot as plt
from matplotlib.patches import Polygon
from matplotlib.collections import PatchCollection
import numpy as np
from multiprocessing import Pool
import os
from time import time
import imageio


def save_screenshot(bottom, left, top, right, target_epsg, shp_path, out_img_path):
    try:
        fig = plt.figure()
        ax = fig.add_subplot(111)
        map = Basemap(
            llcrnrlon=left,
            llcrnrlat=bottom,
            urcrnrlon=right,
            urcrnrlat=top,
            resolution="f",
            epsg="{}".format(target_epsg),
        )

        map.bluemarble()
        # map.arcgisimage(service="ESRI_Imagery_World_2D", xpixels=5000, verbose=True)
        # map.drawmapboundary()
        map.drawcoastlines()
        map.drawcountries()
        shp_name = shp_path.split("/")[-1].split(".")[0]
        shp_path = shp_path.split(".")[0]
        map.readshapefile(shp_path, shp_name)
        patches = []
        for info, shape in zip(
            getattr(map, "{}_info".format(shp_name)), getattr(map, shp_name)
        ):
            patches.append(Polygon(np.array(shape), True))
        # ax.add_collection(
        #     PatchCollection(patches, facecolor="b", edgecolor="k", linewidths=1.0, zorder=2)
        # )
        ax.add_collection(PatchCollection(patches, facecolor="b"))
        # plt.show()
        plt.savefig(out_img_path)
    except Exception as e:
        print("some error encountered in ", shp_path)
        print("error - ", e)


def generate_gif(src_img_dir, out_gif_path, img_duration):
    images = []
    img_num_list = []
    for img_name in os.listdir(src_img_dir):
        if img_name.endswith(".png"):
            img_elev = int(img_name.split(".")[0].split("_")[-1].replace("cm", ""))
            img_num_list.append(img_elev)
            temp_var = img_name.split(".")[0].split("_")
    for img_num in sorted(img_num_list):
        file_path = os.path.join(
            src_img_dir,
            temp_var[0]
            + "_"
            + temp_var[1]
            + "_"
            + "{}cm".format(img_num)
            + "."
            + img_name.split(".")[1],
        )
        images.append(imageio.imread(file_path))
    imageio.mimsave(out_gif_path, images, duration=img_duration)


if __name__ == "__main__":

    # germany bounds
    # left = 3.097656
    # bottom = 45.204642
    # right = 17.512695
    # top = 56.673831
    # india bounds
    left = 68.1766451354
    bottom = 7.96553477623
    right = 97.4025614766
    top = 35.4940095078
    target_epsg = 4326
    num_processes = 3
    src_dir = ""
    out_img_dir = (
        "/home/naman/Desktop/side_projects/world_sea_level_rise/india_batch_screenshots"
    )

    os.makedirs(out_img_dir, exist_ok=True)
    task_list = []

    for shp in os.listdir(src_dir):
        if shp.endswith(".shp"):
            # start_time = time()
            shp_path = os.path.join(src_dir, shp)
            shp_name = shp_path.split("/")[-1].split(".")[0]
            out_img_path = os.path.join(out_img_dir, "{}.png".format(shp_name))
            task_list.append(
                [bottom, left, top, right, target_epsg, shp_path, out_img_path]
            )
    print("total {} screenshots will be generated".format(len(task_list)))
    p = Pool(num_processes)
    p.starmap(save_screenshot, task_list)
    p.close()
    p.join()

    start_time = time()
    generate_gif(
        out_img_dir, os.path.join(out_img_dir, "india_sea_level_rise.gif"), 0.15
    )
    print("took {} seconds".format(time() - start_time))
