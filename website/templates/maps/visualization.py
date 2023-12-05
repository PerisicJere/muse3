import json
import mysql.connector
import folium
from folium.plugins import MarkerCluster
import geocoder

'''library folium
takes all of the locations from database, and makes interactive map out of it

You can search user specific locations by their type
'''

config_file = "connectorConfig.json"
with open(config_file, "r") as f:
    config = json.load(f)
    connection_config = config["mysql"]
    conn = mysql.connector.connect(**connection_config)

m = folium.Map(location=[43.6590368, -70.2569226], tiles='OpenStreetMap', control_scale=True, zoom_start=12)
ipaddress = geocoder.ip('me')
cursor = conn.cursor()
cursor.execute("SELECT latitude, longitude, address, location_name, location_type FROM artLocation")
locations = cursor.fetchall()
conn.close()
markerCluster = MarkerCluster().add_to(m)
for location in locations:
    lat, lon, address, name, type = location
    if lat is not None and lon is not None:
        if type == 'Statue':
            # icon author JM Graphic
            icon_img = "icons/statue.png"
        elif type == 'Sculpture':
            #  icon author Freepik
            icon_img = "icons/sculpture.png"
        elif type == 'Music Venue':
            #  icon author Freepik
            icon_img = "icons/concert.png"
        elif type == 'Museum':
            # icon author Freepik
            icon_img = "icons/museum.png"
        elif type == 'Gallery':
            # icon author Made by Made Premium
            icon_img = 'icons/art-gallery.png'
        elif type == 'Event Venue':
            #  icon author Smashicons
            icon_img = 'icons/gazebo.png'
        popup_content = f"<b>Name:</b> {name}<br><b>Address:</b> {address}<br><b>Type:</b> {type}"
        icon = folium.CustomIcon(
            # icon author iconixar
            icon_image=icon_img,
            icon_size=(40, 40),
            icon_anchor=(22, 22),
            # icon author Iconjam
            shadow_image="icons/shadow.png",
            shadow_size=(40, 10),
            shadow_anchor=(22, -9),
            popup_anchor=(-3, -20),
        )
        folium.Marker(location=[lat, lon], popup=popup_content, icon=icon).add_to(markerCluster)
    else:
        print("Invalid latitude or longitude values. Skipping Marker creation.")

icon = folium.CustomIcon(
    # icon author iconixar
    icon_image="icons/user.png",
    icon_size=(25, 25),
    icon_anchor=(22, 22),
    popup_anchor=(-3, -20),
)
folium.Marker(
    location=ipaddress.latlng, icon=icon, popup=ipaddress.address
).add_to(m)

m.save('map.html')
