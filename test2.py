import mysql.connector
import requests
from bs4 import BeautifulSoup
import json

WIKIPEDIA_URL = "https://en.wikipedia.org/wiki/List_of_cities_in_India_by_population"
LAT_LONG_URLS = [
    "https://www.latlong.net/category/cities-102-15.html",
    "https://www.latlong.net/category/cities-102-15-2.html",
    "https://www.latlong.net/category/cities-102-15-3.html",
    "https://www.latlong.net/category/cities-102-15-4.html",
    "https://www.latlong.net/category/cities-102-15-5.html",
    "https://www.latlong.net/category/cities-102-15-6.html",
    "https://www.latlong.net/category/cities-102-15-7.html",
    "https://www.latlong.net/category/cities-102-15-8.html",
]

TRAIN_STATION_URLS = [
    "https://www.cleartrip.com/trains/stations/list",
    "https://www.cleartrip.com/trains/stations/list?page=2",
    "https://www.cleartrip.com/trains/stations/list?page=3",
    "https://www.cleartrip.com/trains/stations/list?page=4",
    "https://www.cleartrip.com/trains/stations/list?page=5",
]

# MySQL database connection parameters
db_config = {
    "host": "localhost",
    "user": "root",
    "password": "Root_123",
    "database": "ELT_Task",
}

# Create a MySQL connection
connection = mysql.connector.connect(**db_config)
cursor = connection.cursor()

# Create a table for the data
create_table_query = """
CREATE TABLE IF NOT EXISTS city_data (
    # serial_number INT AUTO_INCREMENT PRIMARY KEY,
    city_id INT,
    city_name VARCHAR(255),
    population VARCHAR(255),
    latitude VARCHAR(255),
    longitude VARCHAR(255),
    temperature FLOAT,
    humidity FLOAT,
    wind_speed FLOAT,
    weather_conditions VARCHAR(255),
    train_station VARCHAR(255),
    code VARCHAR(255)
);
"""
cursor.execute(create_table_query)
connection.commit()

# Scrape city data from Wikipedia
def scrape_indian_cities_data(url):
    response = requests.get(url)
    if response.status_code == 200:
        soup = BeautifulSoup(response.text, 'html.parser')
        city_tables = soup.find_all('table', {'class':'wikitable'})
        cities_data = []
        for i, city_table in enumerate(city_tables):
            for row in city_table.find_all('tr')[1:]:
                columns = row.find_all('td')
                if i == 0:  # For the first table
                    city_name = columns[0].text.strip()
                    population = columns[1].text.strip()
                else:  # For the second table
                    city_name = columns[1].text.strip()
                    population = columns[2].text.strip()
                cities_data.append({
                    'city_name': city_name,
                    'population': population
                })
        return cities_data
    else:
        print("Failed to fetch data from Wikipedia.")
        return None

# Scrape latitude and longitude data from latlong.net
def scrape_indian_cities_lat_long(url):
    response = requests.get(url)
    if response.status_code == 200:
        soup = BeautifulSoup(response.text, 'html.parser')
        rows = soup.find_all('tr')
        geo_data = []
        for row in rows:
            cols = row.find_all('td')
            if cols:
                full_location = cols[0].find('a').text
                city_name = full_location.split(',',1)[0]
                latitude = cols[1].text.strip()
                longitude = cols[2].text.strip()
                geo_data.append({
                    'city_name' : city_name,
                    'latitude': latitude,
                    'longitude': longitude
                })
        return geo_data
    else:
        print("Failed to fetch data from Wikipedia.")
        return None

# Combine data
def combine_data(cities_data, geo_data, train_data):
    # Create a new dictionary to store the combined data
    combined_data = {}

    # Add the population data to the combined_data dictionary
    for city in cities_data:
        city_name = city['city_name']
        population = city['population']
        combined_data[city_name] = {'population': population}

    # Add the latitude and longitude data to the combined_data dictionary
    for city in geo_data:
        city_name = city['city_name']
        latitude = city['latitude']
        longitude = city['longitude']
        if city_name in combined_data:
            # If the city is already in the combined_data dictionary, update the latitude and longitude
            combined_data[city_name]['latitude'] = latitude
            combined_data[city_name]['longitude'] = longitude

    # Add the Train Station data to the combined_data dictionary
    for city in train_data:
        city_name = city['city_name']
        train_station = city['station_name']
        code = city['code']
        if city_name in combined_data:
            combined_data[city_name]['train_station'] = train_station
            combined_data[city_name]['code'] = code

    # combined_data = {city: data for city, data in combined_data.items() if 'population' in data and 'latitude' in data and 'longitude' in data}
    combined_data = {city: {**data, 'train_station': data['train_station'], 'code': data['code']} 
        for city, data in combined_data.items() 
        if 'population' in data and 'latitude' in data and 'longitude' in data 
        and 'train_station' in data and 'code' in data
    }   
    return combined_data

# Convert Kelvin to Celsius
def kelvin_to_celsius(kelvin):
    return kelvin - 273.15

# Get weather data
def get_weather(lat, lon):
    # Define OpenWeather API key
    api_key = 'a45af407131ee0d46d78d42cedc8e1c7'
    # api_key = os.getenv('OPENWEATHER_API_KEY')

    try:
        # Make a GET request to the OpenWeather API
        response = requests.get(f"https://api.openweathermap.org/data/2.5/weather?lat={lat}&lon={lon}&appid={api_key}")

        # Check if the request was successful
        if response.status_code == 200:
            try:
                weather_data = response.json()

                # Extract the necessary data
                temperature_kelvin = weather_data['main']['temp']
                humidity = weather_data['main']['humidity']
                wind_speed = weather_data['wind']['speed']
                weather_conditions = weather_data['weather'][0]['description']
                city_id = weather_data['id']

                # Convert temperature to Celsius
                temperature_celsius = kelvin_to_celsius(temperature_kelvin)

                # Return the data
                return {
                    'city_id': city_id,
                    'temperature': temperature_celsius,
                    'humidity': humidity,
                    'wind_speed': wind_speed,
                    'weather_conditions': weather_conditions
                }
            except json.JSONDecodeError:
                print("Error: Response is not valid JSON")
                return None
            except KeyError:
                print("Error: Some necessary data is missing in the response")
                return None
        else:
            print(f"Failed to get weather data for Latitude: {lat}, Longitude: {lon}. Status code: {response.status_code}, Response: {response.text}")
            return None
    except requests.exceptions.RequestException as e:
        print(f"Error: {e}")
        return None

# Fetch station data
def fetch_station_data(url):
    train_station = []
    with requests.Session() as s:
        s.headers.update({'User-Agent': 'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:15.0) Gecko/20100101 Firefox/15.0.1'})
        response = s.get(url)
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')
            table = soup.find('table')
            rows = table.find_all('tr')
            for row in rows:
                cols = row.find_all('td')
                if cols:
                    code = cols[0].text.strip()
                    station_name = cols[1].text.strip()
                    city_name = cols[2].text.strip()
                    train_station.append({
                        'city_name': city_name,
                        'station_name': station_name,
                        'code': code  
                    })
        else:
            print(f"Failed to fetch data from {url}.")
    return train_station

# Main function to execute ETL pipeline
if __name__ == "__main__":
    # Scrape city data from Wikipedia
    cities_data = scrape_indian_cities_data(WIKIPEDIA_URL)

    # Scrape latitude and longitude data from latlong.net
    geo_data = []
    for url in LAT_LONG_URLS:
        geo_data.extend(scrape_indian_cities_lat_long(url))

    train_data = []
    for url in TRAIN_STATION_URLS:
        train_data.extend(fetch_station_data(url))

    combined_data = combine_data(cities_data, geo_data, train_data)

    # Get weather data for each city
    for city, data in combined_data.items():
        lat = data["latitude"]
        lon = data["longitude"]
        weather_data = get_weather(lat, lon)
        if weather_data:
            data.update(weather_data)

    # Insert data into the MySQL database
    insert_query = """
    INSERT INTO city_data (city_id, city_name, population, latitude, longitude, temperature, humidity, wind_speed, weather_conditions, train_station, code)
    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s);
    """

    for city, data in combined_data.items():
        try:
            cursor.execute(
                insert_query,
                (
                    # data.get("serial_number",None),
                    data.get("city_id", None),
                    city,
                    data.get("population", ""),
                    data.get("latitude", ""),
                    data.get("longitude", ""),
                    data.get("temperature", None),
                    data.get("humidity", None),
                    data.get("wind_speed", None),
                    data.get("weather_conditions", ""),
                    data.get("train_station", ""),
                    data.get("code", ""),
                ),
            )
        except mysql.connector.Error as err:
            print(f"Error: {err}")

    # Commit the changes and close the connection
    connection.commit()
    cursor.close()
    connection.close()
