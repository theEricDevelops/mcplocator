import re
import geojson

# Decode the Unicode string
coord_string = "N42\u00b0 55' W122\u00b0 08'"

# Define the regular expression pattern
pattern = r"([NS])(\d+)\u00b0\s(\d+)'\s([EW])(\d+)\u00b0\s(\d+)'"

# Use the pattern to extract the degrees and minutes
match = re.match(pattern, coord_string)
lat_dir, lat_deg, lat_min, lon_dir, lon_deg, lon_min = match.groups()

# Convert the degrees and minutes to decimal degrees
latitude = int(lat_deg) + int(lat_min)/60
longitude = int(lon_deg) + int(lon_min)/60

# Adjust the signs based on the direction
if lat_dir == 'S':
    latitude = -latitude
if lon_dir == 'W':
    longitude = -longitude

# Create the GeoJSON point object
point = geojson.Point((longitude, latitude))

print(point)