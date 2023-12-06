# muse

- muse is Portland, ME art directory, it has interactive map, it can handle user registration, login, and logout.
- Map is made using folium library, and it displays location, locations can be accessed using address, name, or location type.
- Top reviewers displays all of our top reviewers, profile is user profile with its activity.
- Delete account activates trigger that deletes account, and logout works as you would think.
## Install requirements
```bash
pip install -r requirements.txt
```

## Running The App
- To run if you have database set-up.
```bash
python main.py
```
- if you don't have database set-up, use:
```bash 
python create_tables.py
python insert_into_tables.py
```
- Additionally, data makers are included, so you can generate as many reviews and users you want.
- All the csv files are provided.

## Authors
- William Lago
- Kyrin Kalonji
- Jere Perisic