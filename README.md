# muse

- muse is Portland, ME art directory, it has interactive map, it can handle user registration, login, and logout.
- Map is made using folium library, and it displays location, locations can be accessed using address, name, or location type.
- Top reviewers displays all of our top reviewers, profile is user profile with its activity.
- Delete account activates trigger that deletes account, and logout works as you would think.
## Install requirements
```bash
pip install -r requirements.txt
```
## Database setup
- if you don't have database set-up, use:
- Inside our code there are two json files for database config
- First json is called connectorConfig.json, and it is used for mysql connection, second is called config.json, and it's used with SQLAlchemy.
```bash
python create_tables.py
python insert_into_tables.py
```
- If the code was properly cloned, and both jsons were set up properly, this commands should work.
- Additionally, data makers are included, so you can generate as many reviews and users you want.
- Data makers just need to be run, and they produce csv files.
- All the csv files are provided.
- 
## Running The App
- To run if you have database set-up.
```bash
python main.py
```

## Authors
- William Lago
- Kyrin Kalonji
- Jere Perisic