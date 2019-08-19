"""
GEOGRAPHIC HEATMAP OF DEPOSIT CONCENTRATIONS

AUTHOR:     Gerard Mazi
EMAIL:      gerard.mazi@gmail.com
PHONE:      862.221.2477
"""

import pandas as pd
import folium
import json
import requests

#################################################################################################################
# JSON FILE PREP
# Import zip codes from json file and add zip codes to complete dataset
url = 'https://raw.githubusercontent.com/OpenDataDE/State-zip-code-GeoJSON/master/'

states = [
    json.loads(requests.get(
        url + 'wa_washington_zip_codes_geo.min.json'
    ).text),
    json.loads(requests.get(
        url + 'or_oregon_zip_codes_geo.min.json'
    ).text),
    json.loads(requests.get(
        url + 'ca_california_zip_codes_geo.min.json'
    ).text),
    json.loads(requests.get(
        url + 'hi_hawaii_zip_codes_geo.min.json'
    ).text)
]

# Aggregate all features of targeted json files
all_zip = []
for s in states:
    for i in range(len(s['features'])):
        all_zip.append(s['features'][i])
del s, i, states, url

# Create a json file out of the aggregated features
geojson = dict.fromkeys(['type','features'])           # Empty json file
geojson['type'] = 'FeatureCollection'                  # Assignment to 'type' element
geojson['features'] = all_zip                          # Assignment to 'features' element

# Save updated JSON object
open('geojsondata.json',
     'w').write(
    json.dumps(
        geojson,
        sort_keys=True,
        indent=4,
        separators=(',', ': ')
    )
)

del geojson, all_zip

################################################################################################################
# ANALYSIS

# Raw data
geo = pd.read_csv('geo.csv')

# Data for analytics
codes = geo.loc[
    geo.PrimaryAddressCounty.isin(['SAN BERNARDINO']),
    ['PrimaryAddressPostalCode','CurrentLedgerBalance']
]

# Aggregate deposits by zip code
codes = codes.groupby(
    'PrimaryAddressPostalCode',
    as_index = False
).sum()

# Load json file saved
with open('geojsondata.json') as json_file:
    geodata = json.load(json_file)

# Remove Zip codes not in dataset
geozips = []
for i in range(len(geodata['features'])):
    if geodata['features'][i]['properties']['ZCTA5CE10'] in list(codes['PrimaryAddressPostalCode'].unique()):
        geozips.append(geodata['features'][i])

# Create new JSON objects
new_json = dict.fromkeys(['type','features'])           # Empty json file
new_json['type'] = 'FeatureCollection'                  # Assignment to 'type' element
new_json['features'] = geozips                          # Assignment to 'features' element

# Save updated JSON object
open('cleaned_geodata.json',
     'w').write(
    json.dumps(
        new_json,
        sort_keys=True,
        indent=4,
        separators=(',', ': ')
    )
)

del geozips, geodata, json_file, new_json, i

# Read updated GEO data
final_geo_data = 'cleaned_geodata.json'

# Import branch coordinates
branch = pd.read_csv('branch.csv', encoding = "ISO-8859-1")

coord = list(
    zip(
        list(
            branch['Lat']
        ),
        list(
            branch['Long']
        ),
        list(
            branch['Branch']
        )
    )
)

# Create choropleth
map = folium.Map(
    location=[48, -122],
    zoom_start=8
)

folium.Choropleth(
    geo_data = final_geo_data,
    data = codes,
    columns = ['PrimaryAddressPostalCode','CurrentLedgerBalance'],
    key_on = 'feature.properties.ZCTA5CE10',
    fill_color = 'YlOrRd',
    fill_opacity=0.7,
    line_opacity=0.6,
    legend_name='Deposits by Zip Code'
).add_to(map)

for i in coord:
    folium.Marker(
        location=[
            i[0],
            i[1]
        ],
        popup=i[2]
    ).add_to(map)

map.save("./map.html")
