import re
from geojson import Point

# Decode the Unicode string
coord_string = "36\u00b011\u203228\u2033N 111\u00b048\u203214\u2033W"

# Define the regular expression pattern
pattern = r"(\d+)\u00b0(\d+)\u2032(\d+)\u2033([NS])\s(\d+)\u00b0(\d+)\u2032(\d+)\u2033([EW])"

# Use the pattern to extract the degrees, minutes, and seconds
match = re.match(pattern, coord_string)
lat_deg, lat_min, lat_sec, lat_dir, lon_deg, lon_min, lon_sec, lon_dir = match.groups()

# Convert the degrees, minutes, and seconds to decimal degrees
latitude = round(int(lat_deg) + int(lat_min)/60 + int(lat_sec)/3600, 6)
longitude = round(int(lon_deg) + int(lon_min)/60 + int(lon_sec)/3600, 6)

# Adjust the signs based on the direction
if lat_dir == 'S':
    latitude = -latitude
if lon_dir == 'W':
    longitude = -longitude

coordinates = Point((longitude, latitude))

print(f"Point Coordinate: {coordinates}")