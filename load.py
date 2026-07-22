from pathlib import Path

def load_weather(df):

    Path("output").mkdir(exist_ok=True)

    df.to_csv(
        "output/manny_weather.csv",
        index=False
    )

    print("\nCSV saved successfully!")