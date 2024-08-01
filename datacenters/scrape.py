import requests
from bs4 import BeautifulSoup
import pandas as pd
import time
import numpy as np

# Base URL of the initial page
base_url = 'https://www.datacenters.com/locations'

# Function to get the HTML content of a page
def get_html(url):
    response = requests.get(url)
    if response.status_code == 200:
        return response.text
    return None

# Function to parse the initial page and extract links to individual data center pages
def get_data_center_links(page_number):
    url = f'{base_url}?page={page_number}'
    html = get_html(url)
    soup = BeautifulSoup(html, 'html.parser')
    links = []
    grid = soup.find_all('div', class_='LocationsIndex__tiles__Sc6sW')
    for grid_item in grid[0].find_all('div', class_='LocationTile__location__tZKRS'):  # Adjust the class name accordingly
        a_tag = grid_item.find('a')
        if a_tag:
            links.append(a_tag['href'])
    return links

# Function to extract data from an individual data center page
def extract_data_center_info(url):
    html = get_html(url)
    import pdb
    pdb.set_trace()
    try:
        soup = BeautifulSoup(html, 'html.parser')
    except:
        print('Page not found! Skipping!')
        pass  # page not found
    try:
        info = soup.find('div', class_='LocationShow__sidebar__Pqjuu')
    except:
        return {}
    try:
        name = info.find('a', class_='LocationShowSidebar__sidebarProviderLink__CRcRB').text.lstrip('View ')
    except:
        name = np.nan
    try:
        location = info.find('span', class_='LocationShowSidebar__sidebarAddress__AZdxu').text.split(',')
    except:
        location = np.nan

    if location:
        try:
            country = location[-1]
        except IndexError:
            country = np.nan
        try:
            city = location[-2]
        except IndexError:
            city = np.nan
        try:
            town = location[-3]
        except IndexError:
            town = np.nan
        try:
            address = location[-4]
        except IndexError:
            address = np.nan

    data_dict = {
        'name': name,
        'country': country,
        'city': city,
        'town': town,
        'address': address,
        'total space (sqft)': np.nan,
        'colocation space (sqft)': np.nan,
        'total power (MW)': np.nan,
    }

    try:
        stats = info.find('div', class_='LocationShowSidebar__sidebarStats__OxlOT')
    except:
        return data_dict
    for i, stat in enumerate(stats.find_all('div', class_='LocationShowSidebarStat__statContainer__LPgsu')):
        if i < 3:
            stat_text = stat.find_all('div')[-1].text
            stat_text = stat_text.split(' ')
            try:
                data_dict[f'{stat_text[2]} {stat_text[3]} ({stat_text[1]})'] = f'{stat_text[0]}'
            except IndexError:
                pass  # missing data for this stat
    return data_dict

# Main script to collect all data
def main():
    data_centers = []
    for page in range(1, 86):  # Assuming there are 85 pages
        print(f'Scraping page {page}')
        links = get_data_center_links(page)
        for i, link in enumerate(links):
            print(f'    link {i}')
            data_center_url = f'https://www.datacenters.com{link}'
            data_center_info = extract_data_center_info(data_center_url)
            data_centers.append(data_center_info)
            time.sleep(1)  # To prevent overwhelming the server with requests
        df = pd.DataFrame(data_centers)
        df.to_csv(f'data_centers_{page}.csv', index=False)
        data_centers = []
    return data_centers

# Run the main script and store the results in a DataFrame
if __name__ == '__main__':
    data_centers = main()
    df = pd.DataFrame(data_centers)
    df.to_csv('data_centers.csv', index=False)
    print(df)

