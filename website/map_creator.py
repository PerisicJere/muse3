import json
import mysql.connector
import folium
from folium.plugins import MarkerCluster
import geocoder

def create_folium_map(selected_type='all', search_query=None):
    config_file = "connectorConfig.json"
    with open(config_file, "r") as f:
        config = json.load(f)
        connection_config = config["mysql"]
        conn = mysql.connector.connect(**connection_config)

    m = folium.Map(location=[43.6590368, -70.2569226], tiles='OpenStreetMap', control_scale=True, zoom_start=12)
    ipaddress = geocoder.ip('me')
    cursor = conn.cursor()

    # Modify the SQL query to consider the search query
    if search_query:
        cursor.execute("SELECT latitude, longitude, address, location_name, location_type FROM artLocation WHERE address LIKE %s OR location_name LIKE %s", (f"%{search_query}%", f"%{search_query}%",))
    else:
        cursor.execute("SELECT latitude, longitude, address, location_name, location_type FROM artLocation")

    locations = cursor.fetchall()
    conn.close()
    markerCluster = MarkerCluster().add_to(m)

    for location in locations:
        lat, lon, address, name, location_type = location
        if lat is not None and lon is not None:
            if selected_type == 'all' or location_type == selected_type:
                if location_type == 'Statue':
                    icon_img = "website/icons/statue.png"
                elif location_type == 'Sculpture':
                    icon_img = "website/icons/sculpture.png"
                elif location_type == 'Music Venue':
                    icon_img = "website/icons/concert.png"
                elif location_type == 'Museum':
                    icon_img = "website/icons/museum.png"
                elif location_type == 'Gallery':
                    icon_img = 'website/icons/art-gallery.png'
                elif location_type == 'Event Venue':
                    icon_img = 'website/icons/gazebo.png'
                else:
                    # icon by Freepik
                    icon_img = 'website/icons/paint.png'
                popup_content = f"<b>Name:</b> {name}<br><b>Address:</b> {address}<br><b>Type:</b> {location_type}"
                popup = folium.Popup(popup_content, max_width=300)
                icon = folium.CustomIcon(
                    icon_image=icon_img,
                    icon_size=(40, 40),
                    icon_anchor=(22, 22),
                    shadow_image="website/icons/shadow.png",
                    shadow_size=(40, 10),
                    shadow_anchor=(22, -9),
                    popup_anchor=(-3, -20),
                )
                folium.Marker(location=[lat, lon], popup=popup, icon=icon).add_to(markerCluster)
        else:
            print(f"Invalid latitude or longitude values for location '{name}'. Skipping Marker creation.")

    icon = folium.CustomIcon(
        icon_image="website/icons/user.png",
        icon_size=(25, 25),
        icon_anchor=(22, 22),
        popup_anchor=(-3, -20),
    )
    folium.Marker(
        location=ipaddress.latlng, icon=icon, popup=ipaddress.address
    ).add_to(m)

    m.save('website/templates/map_for_use.html')

    return m

