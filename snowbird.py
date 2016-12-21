import os
import time
import shutil
from bs4 import BeautifulSoup
import requests

SNOWBIRD_URL = 'http://www.snowbird.com'
CAMS_FOLDER = "/tmp/cams"
CAM_TIMEOUT = 1000 # seconds

def fetch_weather():
    try:
        r = requests.get(SNOWBIRD_URL + "/mountain-report/")
        return r.text
    except Exception as e:
        print("Error fetching %s: %s" % (SNOWBIRD_URL, e))

def parse_weather(html_doc):

    output = {}

    try:
        soup = BeautifulSoup(html_doc, 'html.parser')        
        snowfall = soup.find_all('div', {'class': 'total-inches'})
        conditions = soup.find_all('div', {'class': 'condition-value'})
        timestamp = soup.find('div', {'class': 'current-conditions'}).find('div', {'class': 'timestamp'}).contents[0]
        icon = soup.find_all('img', {'class': 'retina condition-icon'})[0].attrs["src"]
        cams = soup.find('div', {'class': 'slideshow-content'}).find_all('div', {'class': 'slideshow-photo'})

        output_cams = []
        for cam in cams:
            name = cam.find('div', {'class': 'cam-info'}).find('h3').contents[0]
            url = cam.find('img', {'class': 'retina'})['src']
            output_cams.append({'name': name, 'url': url})
            
        for item in snowfall:
            parent = item.parent.attrs['id']
            contents = item.contents[0]
            output[parent] = contents

        for item in conditions:
            parent = item.parent.attrs['id']
            contents = item.contents[0]
            output[parent] = contents

        output['timestamp'] = timestamp
        output['icon_url'] = icon
        output['cams'] = output_cams

    except Exception as e:
        print("Error parsing html: %s" % e)

    return output

def fetch_icon(url):
    basename = os.path.basename(url)
    if not os.path.exists(basename):
        response = requests.get(SNOWBIRD_URL + url, stream=True)
        with open("/tmp/" + basename, 'wb') as out_file:
            shutil.copyfileobj(response.raw, out_file)
    return basename

def fetch_webcams(cams):

    if not os.path.exists(CAMS_FOLDER):
        os.mkdir(CAMS_FOLDER)

    for cam in cams:
        # basename = os.path.basename(cam['url'])
        local_path = os.path.join(CAMS_FOLDER, cam['name'].replace(" ", "_")) + ".jpg"

        if not os.path.exists(local_path) or time.time() - os.path.getmtime(local_path) > CAM_TIMEOUT:
            print("Downloading new <%s>" % cam['name'])
            response = requests.get(SNOWBIRD_URL + cam['url'], stream=True)
            with open(local_path, 'wb') as out_file:
                shutil.copyfileobj(response.raw, out_file)
        else:
            print("Cam <%s> is up to date" % cam['name'])

if __name__ == "__main__":
    html = fetch_weather()
    output = parse_weather(html)
    # output['icon_basename'] = fetch_icon(output['icon_url'])

    print(output)

    fetch_webcams(output['cams'])