from flask import Flask, render_template, Response
import mysql.connector
import csv
from io import StringIO

app = Flask(__name__)

# MySQL database connection parameters
db_config = {
    "host": "localhost",
    "user": "root",
    "password": "Root_123",
    "database": "ELT_Task",
}

def fetch_data_from_database():
    try:
        connection = mysql.connector.connect(**db_config)
        cursor = connection.cursor(dictionary=True)

        # Retrieve data from the database
        query = "SELECT * FROM city_data;"
        cursor.execute(query)
        data = cursor.fetchall()

        return data

    except mysql.connector.Error as err:
        print(f"Error: {err}")
        return None

    finally:
        cursor.close()
        connection.close()

# Home route
@app.route("/")
def home():
    data = fetch_data_from_database()
    return render_template("index.html", data=data)

# Download CSV route
@app.route('/download')
def download_csv():
    data = fetch_data_from_database()

    # Create a CSV file in memory
    csv_buffer = StringIO()
    csv_writer = csv.writer(csv_buffer)

    # Write header
    csv_writer.writerow(["City Name", "Population", "Latitude", "Longitude", "Temperature", "Humidity", "Wind Speed", "Weather Conditions", "Train Station", "Code"])

    # Write data rows
    for city in data:
        csv_writer.writerow([city['city_name'], city['population'], city['latitude'], city['longitude'], city['temperature'], city['humidity'], city['wind_speed'], city['weather_conditions'], city['train_station'], city['code']])

    # Create a response with CSV MIME type
    response = Response(csv_buffer.getvalue(), mimetype='text/csv')
    response.headers["Content-Disposition"] = "attachment; filename=city_data.csv"

    return response

if __name__ == "__main__":
    app.run(debug=True, port=5001)
