from extract import extract_weather
from transform import transform_weather
from load import load_weather

def main():

    print("Starting ETL Pipeline...\n")

    weather = extract_weather()

    df = transform_weather(weather)

    load_weather(df)

    print("\nPipeline Complete!")

if __name__ == "__main__":
    main()