import os
import psycopg2
import requests
from flask import Flask, jsonify

app = Flask(__name__)

# Get Managed Identity Token
def get_access_token():
    identity_endpoint = os.getenv("MSI_ENDPOINT")
    identity_header = os.getenv("MSI_SECRET")

    if not identity_endpoint or not identity_header:
        raise Exception("Managed Identity variables not set.")

    token_url = f"{identity_endpoint}?resource=https://ossrdbms-aad.database.windows.net&api-version=2017-09-01"
    headers = {"Secret": identity_header}
    response = requests.get(token_url, headers=headers)

    if response.status_code != 200:
        raise Exception(f"Failed to get token: {response.text}")

    return response.json()["access_token"]

# Connect to PostgreSQL using Managed Identity
def get_db_connection():
    access_token = get_access_token()

    conn = psycopg2.connect(
        dbname="your_database_name",  # Change to your PostgreSQL database
        user="your_postgres_admin@your_server_name",  # Change accordingly
        host="your_server_name.postgres.database.azure.com",  # Change accordingly
        port=5432,
        password=access_token,
        sslmode="require"
    )
    return conn

@app.route("/")
def home():
    return jsonify({"message": "Flask App running on Azure Web App!"})

@app.route("/testdb")
def test_db():
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT NOW();")
        result = cursor.fetchone()
        cursor.close()
        conn.close()
        return jsonify({"message": "Database Connection Successful!", "timestamp": result[0]})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=80, debug=True)
