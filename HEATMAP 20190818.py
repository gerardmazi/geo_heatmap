"""
GEOGRAPHIC HEATMAP OF DEPOSIT CONCENTRATIONS

AUTHOR:     Gerard Mazi
EMAIL:      gerard.mazi@gmail.com
PHONE:      862.221.2477
"""

import pandas as pd
import numpy as np
import folium
import json
import requests
from geopy.geocoders import Nominatim
from geopy.exc import GeocoderTimedOut
import re
from time import sleep

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
    geo.BranchName.isin(['Glendora']),
    ['PrimaryAddressPostalCode','Balance']
]

# Aggregate deposits by zip code
codes = codes.groupby(
    'PrimaryAddressPostalCode',
    as_index = False
).sum()

# Load json file saved
with open('geojsondata.json') as json_file:
    geodata = json.load(json_file)

# Remove Zip codes not in dataset to prevent plotting non relevant zip codes
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
            branch['Latitude_b']
        ),
        list(
            branch['Longitude_b']
        ),
        list(
            branch['BranchName']
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
    columns = ['PrimaryAddressPostalCode','Balance'],
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

############################################################################################################
# DISTANCE FROM BRANCH

# Raw dataset
geo = pd.read_csv('geo.csv')
branch = pd.read_csv('branch.csv', encoding = "ISO-8859-1")

# Footprint states
footprint = geo[geo.PrimaryAddressStateCode.isin(['WA','OR','CA','HI'])].reset_index(drop=True)

# Remove APT number from addresses as that won't get a location hit
Address1 = []
for i in footprint.iloc[:,0]:
    Address1.append(re.sub(' #.*', '', i))
Address2 = []
for i in Address1:
    Address2.append(re.sub(' APT.*', '', i))
Address3 = []
for i in Address2:
    Address3.append(re.sub(' UNIT.*', '', i))
Address4 = []
for i in Address3:
    Address4.append(re.sub(' SUIT.*', '', i))
Address5 = []
for i in Address4:
    Address5.append(re.sub(' SPC .*', '', i))
del Address1, Address2, Address3, Address4

address = pd.DataFrame({'Address': Address5})

footprint = pd.concat([footprint, address], axis=1)

# Obtain Address and Zip code
footprint['FinalAddress'] = footprint.Address + ' ' + footprint.PrimaryAddressPostalCode

# Obtain coordinates for each customer address
geolocator = Nominatim()
coordinates = []
for f in footprint['FinalAddress'].tolist():
    try:
        temp_out = {}
        temp_run = geolocator.geocode(f, timeout=10)
        try:
            temp_out['Latitude'] = temp_run.latitude
        except:
            temp_out['Latitude'] = ''
        try:
            temp_out['Longitude'] = temp_run.longitude
        except:
            temp_out['Longitude'] = ''
        sleep(1)
        coordinates.append(temp_out)
    except GeocoderTimedOut:
        temp_out['Latitude'] = ''
        temp_out['Longitude'] = ''

# Save coordinates
import pickle
with open('coordinates.pkl', 'wb') as f:
    pickle.dump(coordinates, f)
with open("coordinates.pkl", "rb") as fp:
    coordinates = pickle.load(fp)

# Merge coordinates into the footprint dataframe
Latitude, Longitude = [],[]
for i in range(len(coordinates)):
    Latitude.append(coordinates[i]['Latitude'])
    Longitude.append(coordinates[i]['Longitude'])

footprint['Latitude'] = Latitude
footprint['Longitude'] = Longitude

# Cleanup - Delete missing coordinates
footprint = footprint[footprint.Latitude!='']

# Merge branch coordinates
footprint = pd.merge(
    footprint,
    branch[['BranchName','Latitude_b','Longitude_b']],
    how='left',
    on='BranchName'
)

# Calculate distance in miles
footprint['Distance'] = pd.to_numeric(
    (
            (
                    (
                            (footprint.Latitude - footprint.Latitude_b)**(2)
                    )+
                    (
                            (footprint.Longitude - footprint.Longitude_b)**(2)
                    )
            )**(0.5)
    )*100*0.621371
)

# Cleanup - Remove distances > 1000 miles
footprint = footprint[footprint.Distance < 1000]

# Summary Metrics
dist_summary = pd.DataFrame(
    {
        '25 Percentile': footprint.groupby('BranchName')['Distance'].quantile(0.25),
        'Mean': footprint.groupby('BranchName')['Distance'].mean(),
        'Median': footprint.groupby('BranchName')['Distance'].median(),
        '75 Percentile': footprint.groupby('BranchName')['Distance'].quantile(0.75),
        'Branch Balance': geo.groupby('BranchName')['Balance'].sum()
    }
)

branch.groupby(['BranchName','State'])['BranchName'].count()