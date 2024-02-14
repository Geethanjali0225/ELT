from flask import Flask, render_template
import mysql.connector

app = Flask(__name__)

# MySQL database connection parameters
db_config = {
    "host": "localhost",
    "user": "root",
    "password": "Root_123",
    "database": "ELT_Task",
}

# Home route
@app.route("/")
def home():
    try:
        connection = mysql.connector.connect(**db_config)
        cursor = connection.cursor(dictionary=True)

        # Retrieve data from the database
        query = "SELECT * FROM city_data;"
        cursor.execute(query)
        data = cursor.fetchall()

        return render_template("index.html", data=data)

    except mysql.connector.Error as err:
        return f"Error: {err}"

    finally:
        cursor.close()
        connection.close()

if __name__ == "__main__":
    app.run(debug=True, port=5001)
