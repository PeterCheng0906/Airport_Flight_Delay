from datetime import datetime
import psycopg2
from psycopg2.extras import RealDictCursor
from flask import Flask, jsonify, request

app = Flask(__name__)


## Create PostgreSQL Connection

def SQL_conn():
    return psycopg2.connect(
        host="jhu_docker-postgres-1",
        port=5432,
        database="jhu",
        user="jhu",
        password="jhu123"
    )

## Create Aggregated PostgreSQL View:

def airport_daily_view():
    conn = SQL_conn()
    cur = conn.cursor()

    cur.execute("""DROP VIEW IF EXISTS airport_daily_status;""")
    
    cur.execute("""
        CREATE VIEW airport_daily_status AS
        SELECT

            -- Airport Information
            airports.iata_code,
            airports.airport,
            airports.municipality,
            airports.iso_region,
            weather.time AS report_date,

            -- Weather Information
            weather.weather_code,
            weather.temperature_2m_mean,
            weather.cloud_cover_mean,
            weather.wind_speed_10m_mean,
            weather.relative_humidity_2m_mean,
            weather.precipitation_sum,

            -- Traveler Information
            travelers.approx_passengers,
            travelers.approx_departures,
            travelers.approx_arrivals,

            -- Holiday Information
            -- Name of nearest holiday within 7 days
                COALESCE((SELECT holidays.holiday_name
                        FROM holiday holidays
                        WHERE holidays.date BETWEEN
                              weather.time::DATE - 3
                              AND weather.time::DATE + 3),
                        'No nearby holiday') AS holiday_name,
                        
            -- True when the date is within 7 days of a holiday
            CASE
                WHEN EXISTS (SELECT 1
                    FROM holiday holidays
                    WHERE holidays.date BETWEEN
                          weather.time::DATE - 3
                          AND weather.time::DATE + 3)
                THEN TRUE
                ELSE FALSE
            END AS is_holiday,

            -- Aggregated Flight Totals
            COUNT(flights.flight_id) AS total_flights,

            -- Average Delays
            ROUND(AVG(flights.dep_delay), 2)::DOUBLE PRECISION AS average_departure_delay,

            ROUND(AVG(flights.arr_delay), 2)::DOUBLE PRECISION AS average_arrival_delay,

            -- Flights Delayed by at least 15 minutes
            COUNT(flights.flight_id) FILTER (WHERE flights.dep_delay >= 15) AS departures_delayed_15_min,

            COUNT(flights.flight_id) FILTER (WHERE flights.arr_delay >= 15) AS arrivals_delayed_15_min,

            -- Weather-Related Delays
            COUNT(flights.flight_id) FILTER (WHERE flights.delay_due_weather > 0) AS weather_delayed_flights,

            -- # Returns 0 when there are no matching weather-delay values
            COALESCE(SUM(flights.delay_due_weather), 0) AS weather_delay_minutes 

        FROM openmeteo_weather weather
        
        -- JOIN on isolated IATA from airport_time
        JOIN airports_info airports
            ON airports.iata_code = SPLIT_PART(weather.airport_time, '_', 1)

        LEFT JOIN flight_data flights
            ON flights.airport_time = weather.airport_time

        LEFT JOIN yearly_travelers_info travelers
            ON travelers.iata_code = airports.iata_code

        LEFT JOIN holiday holidays
            ON holidays.date = weather.time::DATE

        GROUP BY
            airports.iata_code,
            airports.airport,
            airports.municipality,
            airports.iso_region,
            weather.time,
            weather.weather_code,
            weather.temperature_2m_mean,
            weather.cloud_cover_mean,
            weather.wind_speed_10m_mean,
            weather.relative_humidity_2m_mean,
            weather.precipitation_sum,
            travelers.approx_passengers,
            travelers.approx_departures,
            travelers.approx_arrivals,
            holidays.date,
            holidays.holiday_name,
            holidays.types;
    """)

    conn.commit()
    cur.close()
    conn.close()


## Airport Status Endpoints

@app.route("/api/airport/status", methods=["GET"])
def get_airport_status():
    iata_code = request.args.get("airport", "").strip().upper()
    report_date = request.args.get("date")

    ## Common errors for user-entered fields: 
    if not iata_code:
        return jsonify({"error": "An airport IATA code is required."}), 400

    if len(iata_code) != 3 or not iata_code.isalpha():
        return jsonify({"error": "IATA code must contain three letters."}), 400

    if not report_date:
        return jsonify({"error": "A date parameter is required."}), 400

    conn = SQL_conn()
    cur = conn.cursor(cursor_factory=RealDictCursor) # Returns query as a dictionary

    cur.execute("""
        SELECT *
        FROM airport_daily_status
        WHERE iata_code = %s
        AND report_date = %s;
    """, (iata_code, report_date))

    row = cur.fetchone()

    if row is None:
        return jsonify({"error": (
            "No airport or weather data was found for the requested airport and date.")}), 404

    row["report_date"] = row["report_date"].isoformat()

    result = {
        "iata_code": row["iata_code"],
        "airport": row["airport"],
        "municipality": row["municipality"],
        "region": row["iso_region"],
        "date": row["report_date"],

        "flight_status": {
            "total_flights": row["total_flights"],
            "average_departure_delay": row["average_departure_delay"],
            "average_arrival_delay": row["average_arrival_delay"],
            "departures_delayed_15_min": row["departures_delayed_15_min"],
            "arrivals_delayed_15_min": row["arrivals_delayed_15_min"],
            "weather_delayed_flights": row["weather_delayed_flights"],
            "weather_delay_minutes": row["weather_delay_minutes"]
        },

        "weather": {
            "weather_code": row["weather_code"],
            "temperature_2m_mean": row["temperature_2m_mean"],
            "cloud_cover_mean": row["cloud_cover_mean"],
            "wind_speed_10m_mean": row["wind_speed_10m_mean"],
            "relative_humidity_2m_mean": row["relative_humidity_2m_mean"],
            "precipitation_sum": row["precipitation_sum"]
        },

        "traveler_information": {
            "approx_passengers": row["approx_passengers"],
            "approx_departures": row["approx_departures"],
            "approx_arrivals": row["approx_arrivals"]
        },

        "holiday_information": {
            "is_holiday": row["is_holiday"],
            "holiday_name": row["holiday_name"],
        }
      
    }

    return jsonify(result), 200

    cur.close()
    conn.close()

## Start Flask

if __name__ == "__main__":
    airport_daily_view()

    app.run(debug = True, 
        host="127.0.0.1",
        port=8001,
        use_reloader=False)