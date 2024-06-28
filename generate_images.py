from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from contextlib import contextmanager


html_file_path = "/Users/Nayan/Desktop/work/GIS_Reporting_System/Temp/html/shapefile_map.html"
output_image_path = "/Temp/output/images/test.png"
@contextmanager
def chrome_driver():
    # Set up Chrome options to run headless
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--window-size=1920x1080")  # Optional: Set the window size

    # Initialize the webdriver
    driver = webdriver.Chrome(options=chrome_options)

    try:
        yield driver
    finally:
        # Close the webdriver
        driver.quit()

def capture_html_image(html_file_path = html_file_path, output_image_path = output_image_path):
    with chrome_driver() as driver:
        # Load the HTML file in the browser
        driver.get(f"file://{html_file_path}")

        # Capture a screenshot of the loaded HTML
        driver.save_screenshot(output_image_path)
        print('Capture Successful!!!')

#capture_html_image(html_file_path, output_image_path)
