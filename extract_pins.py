import json
import re
import geojson
import logging

# Create a logger
logger = logging.getLogger(__name__)

# Set the log level
logger.setLevel(logging.INFO)

# Create a file handler
error_handler = logging.FileHandler('error.log')
warn_handler = logging.FileHandler('warn.log')

# Create a logging format
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')

# Set the formatter for the handler
error_handler.setFormatter(formatter)
warn_handler.setFormatter(formatter)

# Add the handler to the logger
logger.addHandler(error_handler)
logger.addHandler(warn_handler)

def convert_to_decimal(parts: list) -> float:
    # Split the coordinate into degrees, minutes, seconds, and direction
    direction = str(parts[0][:1])
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

# Load the JSON file
with open('products/products.json') as f:
    data = json.load(f)

# Extract the required fields
extracted_data = []
for entry in data:
    if entry.get('instore_product_type') == 'pin':
        name = description = instore_id = image_src = place_name = elevation = location = latitude = longitude = coordinates = ''

        name = entry.get('name')
        print(f"Name: {name}")

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
                pattern = r'([NS]?\d{1,3}[°\u00BA]?\s*\d{1,3}[\.\d{0,6}]?[\'\u2019]?\s*\d{1,3}.?\d{0,2}[\'\u201d]{0,2}\s*[NS]?)\s([EW]?\d{1,3}[°\u00BA]?\s*\d{1,3}[\.\d{0,6}][\'\u2019]?\s*\d{1,3}.?\d{0,2}[\'\u201d]{0,2}\s*[EW]?)'
                dec_pattern = r'((?=.*[NS])[NS]?\s*\d+\.\d+[NS]?)\s*((?=.*[EW])[EW]?\s*[-]?\d+\.\d+[EW]?)'
                match = re.search(pattern, description)
                dec_match = re.search(dec_pattern, description)

                if match:
                    print(f"Match found w/first pattern: {match.group(0)}")
                    latitude, longitude = match.group(1), match.group(2)
                    print(f"Latitude: {latitude}")
                    print(f"Longitude: {longitude}")
                    if latitude[-1] in 'NS':
                        latitude = latitude[-1] + latitude[:-1]
                    if longitude[-1] in 'EW':
                        longitude = longitude[-1] + longitude[:-1]
                    coordinates = [convert_to_decimal(latitude.split()), convert_to_decimal(longitude.split())] if latitude and longitude else None
                elif dec_match:
                    print(f"Match found w/second pattern: {dec_match.group(0)}")
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
            pass

        if not coordinates:
            print(f'Error: {name} does not have coordinates')
            logger.warning(f'Warning: {name} does not have coordinates\nDescription: {description}')

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
with open('products/pinss.json', 'w') as f:
    json.dump(extracted_data, f)