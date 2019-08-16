"""
GEOGRAPHIC HEATMAP OF $ CONCENTRATIONS

AUTHOR:     Gerard Mazi
EMAIL:      gerard.mazi@homestreet.com
PHONE:      862.221.2477
"""

import pandas as pd
import folium
import os
import requests

geo = pd.read_csv('geo.csv')

wa = geo.loc[
    geo.PrimaryAddressStateCode=='WA',
    ['PrimaryAddressPostalCode','CurrentLedgerBalance']
]

osm = folium.Map([43, -100], zoom_start=4)

url = 'https://raw.githubusercontent.com/OpenDataDE/State-zip-code-GeoJSON/master/wa_washington_zip_codes_geo.min.json'
zip = requests.get(url)

osm.choropleth(
    geo_str = open(zip.json()).read(),
    data = wa,
    columns = ['PrimaryAddressPostalCode','CurrentLedgerBalance'],
    key_on = 'feature.id',
    fill_color = 'YlGn',
)