import os
import elevation

def download_dem(bounds_left, bounds_bottom, bounds_right, bounds_top, out_tif_path):
    elevation.clip(bounds=(bounds_left, bounds_bottom, bounds_right, bounds_top), output=out_tif_path)
    # clean up stale temporary files and fix the cache in the event of a server error
    elevation.clean()


if __name__ == "__main__":

    bounds_left = 2
    bounds_bottom = 2
    bounds_right = 3
    bounds_top = 3
    out_tif_path = "/home/naman/Desktop/side_projects/world_sea_level_rise/test_dem.tif"

    # download_dem(bounds_left, bounds_bottom, bounds_right, bounds_top, out_tif_path)
    elevation.clip(bounds=(12.35, 41.8, 12.65, 42), output='Rome-DEM.tif')

