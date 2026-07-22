import requests
import pandas as pd

def extract_weather():

    # Read datasets
    flights = pd.read_csv("flights.csv")
    airports = pd.read_csv("airports (2).csv")

    # Find all airports used in the flight dataset
    used_airports = set(flights["ORIGIN"].dropna()).union(
        set(flights["DEST"].dropna())
    )

    # Keep only airports that appear in the flight data
    airports = airports[airports["iata_code"].isin(used_airports)]

    print(f"Downloading weather for {len(airports)} airports...\n")

    url = "https://archive-api.open-meteo.com/v1/archive"

    session = requests.Session()

    weather_data = []

    failed_airports = []

    for airport in airports.itertuples(index=False):

        params = {
            "latitude": airport.latitude_deg,
            "longitude": airport.longitude_deg,
            "start_date": "2019-01-01",
            "end_date": "2023-12-31",
            "daily": [
                "weather_code",
                "temperature_2m_mean",
                "cloud_cover_mean",
                "wind_speed_10m_mean",
                "relative_humidity_2m_mean",
                "precipitation_sum"
            ],
            "temperature_unit": "fahrenheit",
            "wind_speed_unit": "mph",
            "precipitation_unit": "inch",
            "timezone": "auto"
        }

        try:

            response = session.get(url, params=params, timeout=30)

            response.raise_for_status()

            data = response.json()

            data["iata_code"] = airport.iata_code

            weather_data.append(data)

            print(f"Downloaded {airport.iata_code}")

        except Exception:

            failed_airports.append(airport.iata_code)

            print(f"Failed {airport.iata_code}")

    print("\nFinished Downloading\n")

    print(f"Successful Airports: {len(weather_data)}")

    print(f"Failed Airports: {len(failed_airports)}")

    return weather_data