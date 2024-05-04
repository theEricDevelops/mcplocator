import json
import re
import geojson
import logging
import requests
from bs4 import BeautifulSoup

class LevelFilter(logging.Filter):
    def __init__(self, level):
        self.level = level

    def filter(self, logRecord):
        return logRecord.levelno == self.level

# Create a logger
logger = logging.getLogger(__name__)

# Create a file handler
error_handler = logging.FileHandler('error.log', mode='w')
warn_handler = logging.FileHandler('warn.log', mode='w')
info_handler = logging.FileHandler('info.log', mode='w')

# Create filters
warn_filter = LevelFilter(logging.WARNING)
error_filter = LevelFilter(logging.ERROR)

# Add the filters to the handlers
warn_handler.addFilter(warn_filter)
error_handler.addFilter(error_filter)

# Set the log level for the handlers
error_handler.setLevel(logging.ERROR)
warn_handler.setLevel(logging.WARNING)
info_handler.setLevel(logging.INFO)

# Create a logging format
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')

# Set the formatter for the handler
error_handler.setFormatter(formatter)
warn_handler.setFormatter(formatter)
info_handler.setFormatter(formatter)

# Add the handler to the logger
logger.addHandler(error_handler)
logger.addHandler(warn_handler)
logger.addHandler(info_handler)

total_pins = 0
total_errs = 0
total_warn = 0

def convert_to_decimal(parts: list) -> float:
    # Split the coordinate into degrees, minutes, seconds, and direction

    direction = str(parts[0][:1])

    for part in parts:
        # If part contains a non-digit character, remove it
        if not part.isdigit():
            part = re.sub(r"[^0-9.]", "", part)

    # Convert the coordinate to decimal format
    degrees = float(parts[0][1:].replace('°', '').replace('\u00BA', ''))
    minutes = float(parts[1].replace("'", '').replace("\u2019", ''))
    if len(parts) > 2 and parts[2]:
        seconds = float(parts[2].replace("''", '').replace('"', '').replace("\u201d", ''))
    else:
        seconds = 0

    # Convert to decimal format
    decimal_degrees = degrees + (minutes / 60) + (seconds / 3600)

    # Handle direction (N/S and E/W)
    if direction in ['S', 'W']:
        decimal_degrees *= -1

    return decimal_degrees

def get_wiki_coord(name: str) -> str:
    # Replace spaces with underscores to match Wikipedia URL format
    name = name.replace(' ', '_')

    # Get the Wikipedia page
    url = f"https://en.wikipedia.org/wiki/{name}"
    response = requests.get(url)

    # Parse the page with BeautifulSoup
    soup = BeautifulSoup(response.text, 'html.parser')

    # Find the span with class "geo"
    lat_tag = soup.find('span', {'class': 'latitude'})
    lon_tag = soup.find('span', {'class': 'longitude'})

    if lat_tag and lon_tag:
        # If both tags are found, return their contents
        return lat_tag.text, lon_tag.text
    else:
        # If no geo tag is found, return an error message
        return False

# Load the JSON file
with open('products/raw_data/imported_products.json') as f:
    data = json.load(f)

# Extract the required fields
extracted_data = []
for entry in data:
    if entry.get('instore_product_type') == 'pin':
        total_pins += 1
        name = description = instore_id = image_src = place_name = elevation = location = latitude = longitude = coordinates = ''

        name = entry.get('name')
        logger.info(f"Name: {name}")

        description = entry.get('description')

        instore_id = entry.get('instore_id')

        image_src = entry.get('images')[0].get('src') if entry.get('images') else None

        # Extract the required fields using regex
        place_name_match = re.search('Place Name:</span> (.*?)\s*<br>', description)
        place_name = place_name_match.group(1) if place_name_match else None

        elevation_match = re.search('Elevation:</span> (.*?) ft.<br>', description)
        elevation = elevation_match.group(1) if elevation_match else None

        location_match = re.search('Location:</span> (.*?) <br>', description)
        location = location_match.group(1) if location_match else None
        
        try:
            if re.search('Coordinates:', description):
                description = description.encode(encoding='utf-8', errors='ignore').decode()
                pattern = r'([NS]?\d{1,3}\°?\s*\d{1,3}[\.\d{0,6}]?\'?\s*\d{1,3}.?\d{0,2}\'{0,2}\s*[NS]?)\s([EW]?\d{1,3}°?\s*\d{1,3}[\.\d{0,6}]\'?\s*\d{1,3}.?\d{0,2}\'{0,2}\s*[EW]?)'
                dec_pattern = r'((?=.*[NS])[NS]?\s*\d+\.\d+[NS]?)\s*((?=.*[EW])[EW]?\s*[-]?\d+\.\d+[EW]?)'
                match = re.search(pattern, description)
                dec_match = re.search(dec_pattern, description)

                if match:
                    logger.info(f"Match found w/first pattern: {match.group(0)}")
                    latitude, longitude = match.group(1), match.group(2)
                    logger.info(f"Latitude: {latitude}")
                    logger.info(f"Longitude: {longitude}")
                    if latitude[-1] in 'NS':
                        latitude = latitude[-1] + latitude[:-1]
                    if longitude[-1] in 'EW':
                        longitude = longitude[-1] + longitude[:-1]
                    coordinates = [convert_to_decimal(latitude.split()), convert_to_decimal(longitude.split())] if latitude and longitude else None
                elif dec_match:
                    logger.info(f"Match found w/second pattern: {dec_match.group(0)}")
                    latitude, longitude = dec_match.group(1), dec_match.group(2)

                    lat_direction = latitude[0]
                    lon_direction = longitude[0]
                    latitude = latitude[1:]
                    longitude = longitude[1:]
                    if lat_direction == 'S':
                        latitude *= -1
                    if lon_direction == 'W':
                        longitude *= -1
                    coordinates = [latitude, longitude] if latitude and longitude else None
                
                coordinates = geojson.Point(coordinates) if coordinates else None
        except Exception as e:
            logger.error(f"""Error: {e}
                Name: {name}
                Lat: {latitude}
                Lon: {longitude}
                Description: {description}
            """)
            total_errs += 1
            pass

        if not coordinates:
            #try:
            #    coordinates = get_wiki_coord(name)
            #except Exception as e:
            #    logger.error(f"Error: {e}")
            #    total_errs += 1
            #    pass
            #if not coordinates:
                logger.warning(f'Warning: {name} does not have coordinates\nDescription: {description}')
                total_warn += 1
                pass

        extracted_data.append({
            'name': name,
            'place_name': place_name,
            'elevation': elevation,
            'coordinates': coordinates,
            'location': location,
            'instore_id': instore_id,
            'image_src': image_src
        })

# Save the extracted data to a new JSON file
with open('products/extracted_pins.json', 'w') as f:
    json.dump(extracted_data, f)

print(f"Total pins: {total_pins}")
print(f"Total errs: {total_errs}")
print(f"Total warns: {total_warn}")