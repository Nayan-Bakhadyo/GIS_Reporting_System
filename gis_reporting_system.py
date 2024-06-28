import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import folium
import geopandas as gpd
import os
from report_generator import generate_report

#from test import perform_sat_img_clipping
# Global variable to track if shapefile is uploaded
shapefile_uploaded = False
shape_file_path = ''
def upload_shapefile():
    global shapefile_uploaded
    global shape_file_path
    # Open a file dialog to select a shapefile
    file_path = filedialog.askopenfilename(filetypes=[("Shapefile", "*.shp")])
    shape_file_path = file_path
    # Process the selected shapefile
    if file_path:
        shapefile_uploaded = True
        messagebox.showinfo("Success", "Shapefile uploaded successfully!")

        # Enable the "Generate Report" button
        generate_report_button.config(state="normal")

        # Read the shapefile using geopandas
        gdf = gpd.read_file(file_path)
        print(gdf.crs)
        if not gdf.crs.equals("EPSG:4326"):
            gdf['geometry'] = gdf['geometry'].to_crs(epsg=4326)

        # Calculate the bounding box of the shapefile
        bounds = gdf.total_bounds

        # Calculate the center of the bounding box
        center = [(bounds[1] + bounds[3]) / 2, (bounds[0] + bounds[2]) / 2]

        # Create a Folium map centered around the shapefile bounds
        shapefile_map = folium.Map(location=center, zoom_start=10)

        # Add the shapefile data to the map
        folium.GeoJson(gdf).add_to(shapefile_map)

        # Fit the map to the bounds of the shapefile
        shapefile_map.fit_bounds([[bounds[1], bounds[0]], [bounds[3], bounds[2]]])

        # Save the map to an HTML file and open it in the default web browser
        output_html = os.path.join(os.environ["GIS_REPORTING_SYSTEM"], "GIS_Reporting_System/Temp/html/shapefile_map.html")
        shapefile_map.save(output_html)

        print('Opening Shapefile with map!!')

        # Open the HTML file with the default application associated with HTML files
        os.system(f"open {output_html}")

def process_generate_report():
    global shape_file_path
    print(shape_file_path)
    generate_report(shape_file_path)
def main():
    # Create the main window
    root = tk.Tk()
    root.title("GIS Reporting System")

    # Set the size of the window
    root.geometry("700x400")

    # Define custom styles for buttons with increased size
    style = ttk.Style()
    style.configure("Blue.TButton", foreground="black", background="blue",
                    padding=(10, 10, 10, 10))  # Adjust padding for increased size
    style.configure("Red.TButton", foreground="black", background="red",
                    padding=(10, 10, 10, 10))  # Adjust padding for increased size

    # Add a heading
    heading = ttk.Label(root, text="Welcome to GIS Reporting System", font=("Helvetica", 16, "bold"))
    heading.pack(pady=10)

    # Add instructions
    instructions_text = """
    1. Click the Upload Shapefile button and upload .shp file.
    
    2. Once the shapefile is uploaded, verify the shape file.
    
    3. After verification please click Generate Report button to start generating report.
    """
    instructions = tk.Text(root, wrap="word", height=10, width=100, font=("Helvetica", 18))
    instructions.insert(tk.END, instructions_text)
    instructions.config(state="disabled")
    instructions.pack(pady=10)

    # Add a button to upload shapefile
    global upload_shapefile_button
    upload_shapefile_button = ttk.Button(root, text="Upload Shapefile", style="Blue.TButton", command=upload_shapefile)
    upload_shapefile_button.pack(pady=5, padx=100, side=tk.LEFT)

    # Add a button to generate report
    global generate_report_button
    generate_report_button = ttk.Button(root, text="Generate Report", style="Red.TButton", command=process_generate_report)
    generate_report_button.pack(pady=5, padx=40, side=tk.LEFT)
    generate_report_button.config(state="disabled")  # Disable initially

    # Run the Tkinter event loop
    root.mainloop()

if __name__ == "__main__":
    main()
