from tkinter import messagebox
import geopandas as gpd
import matplotlib.pyplot as plt
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from rasterio.mask import mask
import os
import rasterio
from shapely.geometry import Polygon
from tqdm import tqdm
import rasterio.sample, rasterio.vrt
from rasterio.features import shapes
from generate_images import capture_html_image
from docx_report_generator import generate_docx
import folium
from selenium import webdriver
import cv2
import numpy as np
from PIL import Image

global output_folder, output_pdf, progress_bar
global area, meta_pop_2021, pop_density
global area_gdf

output_folder = 'Temp/output/images'
output_pdf = 'Temp/output/pdfs'
input_sat_img = 'assets/sat_img/'
area = 0
meta_pop_2021 = 0
pop_density = 0


def calculate_boundary_area(boundary_shapefile):
    # Read the boundary shapefile
    boundary_gdf = gpd.read_file(boundary_shapefile)

    # Check CRS and reproject if necessary
    if boundary_gdf.crs != 'epsg:32645':  # Assuming UTM Zone 45N
        boundary_gdf = boundary_gdf.to_crs('epsg:32645')  # Reproject to UTM Zone 45N

    # Calculate the area of the boundary shapefile in square kilometers
    area_km2 = boundary_gdf.area.sum() / 1e6  # Convert square meters to square kilometers

    return area_km2
def generate_report(boundary_shapefile):
    print('Inside generate report!!')
    print(boundary_shapefile)
    perform_raster_clipping(boundary_shapefile)
    perform_vector_clipping(boundary_shapefile)
    save_htmls(boundary_shapefile)
    generate_images()
    generate_docx()
    # Generate PDF report
    #generate_pdf_report(output_folder, output_pdf, progress_bar)
    messagebox.showinfo("Report Generated", "Report generated successfully!")

def save_htmls(boundary_shapefile_path):
    boundary_gdf = gpd.read_file(boundary_shapefile_path)
    # Calculate the center of the boundary shapefile
    boundary_center = boundary_gdf.geometry.centroid.unary_union
    # Create a Folium map centered around the boundary
    map_center = [boundary_center.y, boundary_center.x]
    mymap = folium.Map(location=map_center, zoom_start=10)

    # Add boundary layer to the map
    folium.GeoJson(boundary_gdf, name='Tole Boundary').add_to(mymap)

    shape_files = ["GIS_Reporting_System/Temp/output/vector_files/Population_2021_src_Meta.shp",
                   "GIS_Reporting_System/Temp/output/vector_files/Base_Transceiver_Station_BTS_Tower.shp",
                   "GIS_Reporting_System/Temp/output/vector_files/Building_points.shp",
                   "GIS_Reporting_System/Temp/output/vector_files/KUKL_Proposed_Pipeline_Network.shp",
                   "GIS_Reporting_System/Temp/output/vector_files/Existing_KV-WaterSupply_Network.shp",
                   "GIS_Reporting_System/Temp/output/vector_files/Sewer_Network.shp"]

    raster_files = ["GIS_Reporting_System/Temp/output/raster_files/NDVI.tif", "GIS_Reporting_System/Temp/output/raster_files/01_13_23_imagery_clipped.tif",]
    print('Processing Raster HTMLs')
    for raster_file_path in raster_files:
        tiff_file_path = os.path.join(os.environ["GIS_REPORTING_SYSTEM"], raster_file_path)
        file_name = os.path.splitext(os.path.basename(raster_file_path))[0]
        output_path = os.path.join(os.environ["GIS_REPORTING_SYSTEM"],
                                   "GIS_Reporting_System/Temp/output/images/" + file_name + ".png")
        pass

    print('-------Raster HTML generated -----------')

    print('-------Processing Vector HTMLs ----------')

    for url in shape_files:
        file_path = os.path.join(os.environ["GIS_REPORTING_SYSTEM"],url)
        # Split the URL by '/' and get the last element
        file_name = url.split('/')[-1]
        file_name = file_name.split('.')[0]
        output_html= os.path.join(os.environ["GIS_REPORTING_SYSTEM"],
                                   "GIS_Reporting_System/Temp/html/" + file_name + ".html")
        # Read the shapefile using geopandas
        gdf = gpd.read_file(file_path)

        # Calculate the bounding box of the shapefile
        bounds = gdf.total_bounds

        # Calculate the center of the bounding box
        center = [(bounds[1] + bounds[3]) / 2, (bounds[0] + bounds[2]) / 2]

        if file_name == 'Base_Transceiver_Station_BTS_Tower':
            print("Proceeding BTS_Tower Styling!!!")
            # Define marker colors based on Tower_owner attribute
            marker_colors = {
                'NCELL': 'purple',
                'NTC_GSM': 'blue',
                'NTC_CDMA':'black',
            }

            # Define marker icons based on Tower_owner attribute
            marker_icons = {
                'NCELL': 'circle',
                'NTC_GSM': 'marker',
                'NTC_CDMA': 'marker'
            }

            # Add tower locations as markers
            for _, row in gdf.iterrows():
                tower_owner = row['Tower_owne']
                color = marker_colors.get(tower_owner, 'black')
                icon = marker_icons.get(tower_owner, 'marker')
                folium.Marker(
                    location=[row.geometry.y, row.geometry.x],
                    icon=folium.Icon(color=color, icon=icon),
                    popup=f"<b>{row['Tower_owne']}</b>",
                ).add_to(mymap)

            # Create a legend in HTML
            legend_html = """
            <div style="position: fixed; bottom: 50px; left: 50px; z-index:1000; background-color:white; padding: 10px; border: 1px solid black;">
                <p><strong>Legend</strong></p>
                <p><i class="fa fa-circle fa-1x" style="color:purple"></i> NCELL</p>
                <p><i class="fa fa-circle fa-1x" style="color:blue"></i> NTC_GSM</p>
                <p><i class="fa fa-circle fa-1x" style="color:black"></i> NTC_CDMA</p>
            </div>
            """

            # Add legend to the map
            mymap.get_root().html.add_child(folium.Element(legend_html))


        elif file_name == 'KUKL_Proposed_Pipeline_Network' or file_name == 'Existing_KV-WaterSupply_Network':
            print("Proceeding Water Supply Network Styling!!!")
            # Define colors based on the 'TYPE' attribute
            type_colors = {
                'CI': 'red',
                'DI': 'blue',
                'GI': 'green',
                'HDPE': 'orange',
                'PVC': 'purple',
                'PI': 'brown'
            }
            # Add lines to the map with different colors based on the 'TYPE' attribute
            for _, row in gdf.iterrows():
                line_type = row['TYPE']
                color = type_colors.get(line_type, 'black')

                if row.geometry.geom_type == 'LineString':  # Check if it's a LineString
                    coordinates = [(point[1], point[0]) for point in row.geometry.coords]
                    folium.PolyLine(
                        locations=coordinates,
                        color=color,
                        popup=f"<b>{line_type}</b>",
                    ).add_to(mymap)
                elif row.geometry.geom_type == 'MultiLineString':  # Check if it's a MultiLineString
                    for line in row.geometry.geoms:
                        coordinates = [(point[1], point[0]) for point in line.coords]
                        folium.PolyLine(
                            locations=coordinates,
                            color=color,
                            popup=f"<b>{line_type}</b>",
                        ).add_to(mymap)

            # Create a legend in HTML
            legend_html = """
            <div style="position: fixed; bottom: 50px; left: 50px; z-index:1000; background-color:white; padding: 10px; border: 1px solid black;">
                <p>""" +file_name+ """</p>
                <p><strong>Legend</strong></p>
                <p><i class="fa fa-minus fa-1x" style="color:red"></i> CI</p>
                <p><i class="fa fa-minus fa-1x" style="color:blue"></i> DI</p>
                <p><i class="fa fa-minus fa-1x" style="color:green"></i> GI</p>
                <p><i class="fa fa-minus fa-1x" style="color:orange"></i> HDPE</p>
                <p><i class="fa fa-minus fa-1x" style="color:purple"></i> PVC</p>
                <p><i class="fa fa-minus fa-1x" style="color:brown"></i> PI</p>
            </div>
            """
            # Add legend to the map
            mymap.get_root().html.add_child(folium.Element(legend_html))

        elif file_name == '2021_kmc_pop':
            meta_pop_2021 = gdf['VALUE'].sum()
            print("Total population (src. Meta 2021)", meta_pop_2021)
            pop_density = meta_pop_2021/area
            print("Population Density: ", pop_density)

        else:
            # Add the shapefile data to the map
            if gdf.geometry.type.iloc[0] == 'Polygon':  # Check if geometry is Polygon
                folium.GeoJson(gdf).add_to(mymap)
            elif gdf.geometry.type.iloc[0] == 'LineString':  # Check if geometry is LineString
                folium.GeoJson(gdf, style_function=lambda x: {'color': 'red'}).add_to(mymap)
                # Create a legend in HTML
                legend_html = """
                               <div style="position: fixed; bottom: 50px; left: 50px; z-index:1000; background-color:white; padding: 10px; border: 1px solid black;">
                                   <p><strong>Legend</strong></p>
                                   <p><i class="fa fa-minus fa-1x" style="color:red"></i> """ + file_name + """</p>
                               </div>
                               """
                # Add legend to the map
                mymap.get_root().html.add_child(folium.Element(legend_html))
            elif gdf.geometry.type.iloc[0] == 'Point':  # Check if geometry is Point
                # Add the shapefile data to the map with custom marker shape
                for _, row in gdf.iterrows():
                    folium.CircleMarker(
                        location=[row.geometry.y, row.geometry.x],
                        radius=2,  # Adjust the radius as needed
                        color='blue',  # Adjust the color as needed
                        fill=True,
                        fill_color='blue',  # Adjust the fill color as needed
                        fill_opacity=1,  # Adjust the fill opacity as needed
                        popup=f"<b>Point</b>",  # Add a popup if needed
                    ).add_to(mymap)
                    # Create a legend in HTML
                    legend_html = """
                                    <div style="position: fixed; bottom: 50px; left: 50px; z-index:1000; background-color:white; padding: 10px; border: 1px solid black;">
                                        <p><strong>Legend</strong></p>
                                        <p><i class="fa fa-circle fa-1x" style="color:blue"></i> """ + file_name + """</p>
                                    </div>
                                    """
                    # Add legend to the map
                    mymap.get_root().html.add_child(folium.Element(legend_html))
            else:
                folium.GeoJson(gdf).add_to(mymap)
        # Fit the map to the bounds of the shapefile
        mymap.fit_bounds([[bounds[1], bounds[0]], [bounds[3], bounds[2]]])

        mymap.save(output_html)
        # Reset Folium map centered around the boundary
        map_center = [boundary_center.y, boundary_center.x]
        mymap = folium.Map(location=map_center, zoom_start=10)
        # Add boundary layer to the map
        folium.GeoJson(boundary_gdf, name='Tole Boundary').add_to(mymap)

        print('Opening Shapefile with map!!')

        # Open the HTML file with the default application associated with HTML files
        os.system(f"open {output_html}")

    print('VECTOR HTML processed!!!!')

def perform_raster_clipping(shapefile_url):
    #for raster files
    raster_files = ['GIS_Reporting_System/assets/raster/sat_img/01_13_23_imagery_clipped.tif','GIS_Reporting_System/assets/raster/ndvi/NDVI.tif']

    for url in raster_files:
        raster_url = os.path.join(os.environ["GIS_REPORTING_SYSTEM"],
                                  url)
        # Split the URL by '/' and get the last element
        file_name = url.split('/')[-1]
        output_path = os.path.join(os.environ["GIS_REPORTING_SYSTEM"],
                                   "GIS_Reporting_System/Temp/output/raster_files/"+file_name)
        # Read the raster file
        with rasterio.open(raster_url) as src:
            # Get CRS of the raster
            raster_crs = src.crs

            # Read the shapefile
            shapefile_gdf = gpd.read_file(shapefile_url)

            print(shapefile_gdf.crs)
            # Check CRS of the shapefile
            if shapefile_gdf.crs != raster_crs:
                # Reproject the shapefile to match the CRS of the raster
                shapefile_gdf = shapefile_gdf.to_crs(raster_crs)
                print(shapefile_gdf.crs)

            # Convert the shapefile geometry to list of shapely Polygon objects
            geometries = [Polygon(feature['geometry']) for _, feature in shapefile_gdf.iterrows()]

            # Initialize a list to store clipped raster data
            clipped_rasters = []

            # Iterate over geometries and mask the raster using tqdm to show progress
            for geometry in tqdm(geometries, desc="Clipping Raster: "+file_name, unit="polygon"):
                # Mask the raster using the reprojected shapefile
                raster_data, raster_transform = mask(src, [geometry], crop=True)

                # Append the clipped raster data to the list
                clipped_rasters.append(raster_data)

            # Combine all clipped raster data into one array
            clipped_data = sum(clipped_rasters)

            # Get metadata of clipped raster
            raster_meta = src.meta.copy()

        # Update metadata for clipped raster
        raster_meta.update({
            'height': clipped_data.shape[1],
            'width': clipped_data.shape[2],
            'transform': raster_transform,
            'crs': raster_crs  # Ensure CRS is preserved
        })

        # Write the clipped raster to disk
        with rasterio.open(output_path, 'w', **raster_meta) as dst:
            dst.write(clipped_data)

def perform_vector_clipping(boundary_shapefile):
    area = calculate_boundary_area(boundary_shapefile)
    print(f'Area: {area} km.sq')

    shape_files_urls = ["GIS_Reporting_System/assets/vector/shapefiles/07_Water_supply_Network/01_Water_supply Network_Existing/Existing_KV-WaterSupply_Network.shp",
                        "GIS_Reporting_System/assets/vector/shapefiles/07_Water_supply_Network/02_Water_supply_Network_Planned_KUKL/KUKL_Proposed_Pipeline_Network.shp",
                        "GIS_Reporting_System/assets/vector/shapefiles/08_Sewage_Network/Sewer_Network.shp",
                        "GIS_Reporting_System/assets/vector/shapefiles/09_Telecommunication_Network/Base_Transceiver_Station_BTS_Tower.shp",
                        "GIS_Reporting_System/assets/vector/shapefiles/2021_meta_pop/Population_2021_src_Meta.shp",
                        "GIS_Reporting_System/assets/vector/shapefiles/Building_points/Building_points.shp"]

    for url in shape_files_urls:
        shapefile_url = os.path.join(os.environ["GIS_REPORTING_SYSTEM"],
                                                    url)
        # Split the URL by '/' and get the last element
        file_name = url.split('/')[-1]

        output_path = os.path.join(os.environ["GIS_REPORTING_SYSTEM"],
                                   "GIS_Reporting_System/Temp/output/vector_files/"+file_name)
        # Read the boundary shapefile
        boundary_gdf = gpd.read_file(boundary_shapefile)

        # Read the shapefile to be clipped
        shapefile_gdf = gpd.read_file(shapefile_url)

        # Check CRS of the shapefile
        if shapefile_gdf.crs != boundary_gdf.crs:
            # Reproject the shapefile to match the CRS of the boundary shapefile
            boundary_gdf = boundary_gdf.to_crs(shapefile_gdf.crs)

        # Perform clipping
        clipped_gdf = gpd.clip(shapefile_gdf, boundary_gdf.geometry.unary_union)

        if not clipped_gdf.crs.equals("EPSG:4326"):
            clipped_gdf['geometry'] = clipped_gdf['geometry'].to_crs(epsg=4326)

        # Save the clipped shapefile
        clipped_gdf.to_file(output_path)

        #Get information on number of buildings
        # Get information on the number of buildings
        if file_name == 'Building_points.shp':
            num_rows = len(clipped_gdf)
            print("Number of Building in that Area:", num_rows)

        if file_name == 'Population_2021_src_Meta.shp':
            # Sum the values in the 'VALUE' column
            Pop_sum = int(clipped_gdf['VALUE'].sum())
            print("Total Population:", Pop_sum)

def generate_images():
    print('Generating Images')
    html_files = os.path.join(os.environ["GIS_REPORTING_SYSTEM"],
                               "GIS_Reporting_System/Temp/html/")
    image_path = os.path.join(os.environ["GIS_REPORTING_SYSTEM"],
                               "GIS_Reporting_System/Temp/output/images/")

    # Ensure output folders exist
    os.makedirs(image_path, exist_ok=True)

    # Configure Selenium WebDriver
    options = webdriver.ChromeOptions()
    options.add_argument('--headless')  # Run Chrome in headless mode
    driver = webdriver.Chrome(options=options)

    # Loop through HTML files and generate images
    for html_file in os.listdir(html_files):
        if html_file.endswith(".html"):
            html_path = os.path.join(html_files, html_file)
            image_file = os.path.join(image_path, os.path.splitext(html_file)[0] + ".png")
            # Open HTML file in WebDriver
            driver.get("file:///" + html_path)

            # Take screenshot and save as PNG
            driver.save_screenshot(image_file)

    # Quit WebDriver
    driver.quit()
    print('Images Generated successfully!!')

def generate_pdf_report(images_folder, output_pdf, progress_bar):
    c = canvas.Canvas(output_pdf, pagesize=letter)
    # Add images to the PDF
    total_images = len([f for f in os.listdir(images_folder) if f.endswith(".png")])
    for idx, image_file in enumerate(sorted(os.listdir(images_folder)), 1):
        if image_file.endswith(".png"):
            c.drawImage(f"{images_folder}/{image_file}", 100, 100, width=400, height=300)
            c.showPage()
            # Update progress bar
            progress = (idx / total_images) * 100
            progress_bar["value"] = progress
            progress_bar.update()
    c.save()


