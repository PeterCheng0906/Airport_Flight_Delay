import pandas as pd

def transform_weather(weather_json):

    dfs = []

    for airport in weather_json:

        daily = airport["daily"]

        df = pd.DataFrame({

            "IATA_CODE": airport["iata_code"],

            "DATE": daily["time"],

            "WEATHER_CODE": daily["weather_code"],

            "TEMPERATURE_F": daily["temperature_2m_mean"],

            "CLOUD_COVER": daily["cloud_cover_mean"],

            "WIND_SPEED_MPH": daily["wind_speed_10m_mean"],

            "HUMIDITY": daily["relative_humidity_2m_mean"],

            "PRECIPITATION_IN": daily["precipitation_sum"]

        })

        dfs.append(df)

    final_df = pd.concat(dfs, ignore_index=True)

    return final_df