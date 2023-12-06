import mysql.connector
import json

def create_table(config_file, lst_table_descriptions):
    """
    This method takes in the config file path and list of table descriptions and creates tables
    @param lst_table_descriptions: list of table descriptions
    @param config_file:  File Path of the configFile for the database
    """
    with open(config_file, "r") as f:
        config = json.load(f)
    connection_config = config["mysql"]
    data_base = mysql.connector.connect(**connection_config)

    # preparing a cursor object
    cursor_object = data_base.cursor()
    for table_description in lst_table_descriptions:
        cursor_object.execute(table_description)


table_description_user = """
CREATE TABLE IF NOT EXISTS user (
    user_id INT NOT NULL AUTO_INCREMENT,
    password VARCHAR(256) NOT NULL,
    displayName VARCHAR(64) NOT NULL,
    email VARCHAR(64) NOT NULL,
    PRIMARY KEY (user_id)
);

"""

table_description_artlocation = """
CREATE TABLE IF NOT EXISTS artLocation (
    location_id INT NOT NULL AUTO_INCREMENT,
    location_name VARCHAR(64) NOT NULL,
    location_type VARCHAR(64) NOT NULL,
    address VARCHAR(128) NOT NULL,
    description VARCHAR(1024),
    location_image LONGBLOB,
    latitude DOUBLE,
    longitude DOUBLE,
    PRIMARY KEY (location_id)
);

"""

table_description_review = """
CREATE TABLE IF NOT EXISTS review (
    review_id INT NOT NULL AUTO_INCREMENT,
    user_id INT NOT NULL,
    location_id INT NOT NULL,
    stars INT NOT NULL,
    comment VARCHAR(1024),
    review_image LONGBLOB,
    PRIMARY KEY (review_id)
);
"""

lst_table_descriptions = [table_description_user, table_description_artlocation, table_description_review]

create_table(config_file="connectorConfig.json", lst_table_descriptions=lst_table_descriptions)
