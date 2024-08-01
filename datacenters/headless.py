from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import re
import pdb

# Set up the Selenium WebDriver (this example uses Chrome; make sure you have the ChromeDriver installed)
options = webdriver.ChromeOptions()
options.add_argument("--headless")  # Run headless browser

driver = webdriver.Chrome(options=options)

try:
    # Open the webpage
    driver.get('https://www.datacenters.com/sify-technologies-limited-noida-01-dc')

    # Wait until the 'on map' button is clickable and click it
    wait = WebDriverWait(driver, 10)
    map_button = wait.until(EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), 'on map')]")))
    map_button.click()

    # Wait for the coordinates to be loaded in the HTML content
    wait.until(lambda driver: 'LatLng' in driver.page_source)

    # Get the updated page source
    page_source = driver.page_source

    # Define regex pattern to match coordinates
    pattern = re.compile(r'LatLng\(([\d.-]+),\s*([\d.-]+)\)')

    latitude, longitude = None, None

    # Search for the coordinates in the page source
    match = pattern.search(page_source)
    if match:
        latitude = match.group(1)
        longitude = match.group(2)

    # Print the coordinates if found
    if latitude and longitude:
        print(f'Latitude: {latitude}, Longitude: {longitude}')
    else:
        print('Coordinates not found.')

finally:
    # Close the Selenium WebDriver
    driver.quit()
