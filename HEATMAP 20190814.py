"""
GEOGRAPHIC HEATMAP OF $ CONCENTRATIONS

AUTHOR:     Gerard Mazi
EMAIL:      gerard.mazi@homestreet.com
PHONE:      862.221.2477
"""

import pandas as pd
import folium

# Raw data
geo = pd.read_csv('geo.csv')

# Data for analytics
zip = geo.loc[geo.PrimaryAddressStateCode=='WA',
             ['PrimaryAddressPostalCode','CurrentLedgerBalance']]

zip['PrimaryAddressPostalCode'] = zip['PrimaryAddressPostalCode'].astype('str')

zip = zip.groupby('PrimaryAddressPostalCode', as_index = False).sum()

# Create choropleth
osm = folium.Map(location=[47.35, -121.9], zoom_start=8)

url = 'https://raw.githubusercontent.com/OpenDataDE/State-zip-code-GeoJSON/master/wa_washington_zip_codes_geo.min.json'

folium.Choropleth(
    geo_data = url,
    data = zip,
    columns = ['PrimaryAddressPostalCode','CurrentLedgerBalance'],
    key_on = 'feature.properties.ZCTA5CE10',
    fill_color = 'YlGn',
    fill_opacity=0.7,
    line_opacity=0.2,
    legend_name='Deposits by Zip Code'
).add_to(osm)

osm.save("./wa.html")
