import requests
import pandas as pd
from io import StringIO

# Define the URLs and station IDs
urls = [
    "https://www.ndbc.noaa.gov/view_text_file.php?filename=41010h2012.txt.gz&dir=data/historical/stdmet/",
    "https://www.ndbc.noaa.gov/view_text_file.php?filename=42058h2012.txt.gz&dir=data/historical/stdmet/",
    "https://www.ndbc.noaa.gov/view_text_file.php?filename=41013h2012.txt.gz&dir=data/historical/stdmet/",
    "https://www.ndbc.noaa.gov/view_text_file.php?filename=44009h2012.txt.gz&dir=data/historical/stdmet/",
]

# Mapping of station IDs to latitude and longitude
station_coords = {
    "44009": (38.460, -74.692),
    "41013": (33.441, -77.764),
    "42058": (14.512, -75.153),
    "41010": (28.878, -78.467),
}

# Date range for filtering
date_range = pd.date_range("2012-10-20", "2012-10-31").strftime("%Y %m %d").tolist()

# Column names based on the provided format
columns = [
    "YY", "MM", "DD", "hh", "mm", "WDIR", "WSPD", "GST", "WVHT", "DPD", "APD", "MWD",
    "PRES", "ATMP", "WTMP", "DEWP", "VIS", "TIDE"
]

# Initialize an empty list to store dataframes
all_data = []

for url in urls:
    station_id = url.split("filename=")[1][:5]  # Extract station ID from URL
    response = requests.get(url)
    if response.status_code == 200:
        lines = response.text.splitlines()
        
        # Remove header lines
        data_lines = [line for line in lines if not line.startswith("#")]
        
        # Convert to DataFrame
        df = pd.read_csv(StringIO("\n".join(data_lines)), delim_whitespace=True, names=columns, skiprows=1)
        
        # Ensure date columns are integers before formatting
        df["YY"] = df["YY"].astype(int)
        df["MM"] = df["MM"].astype(int)
        df["DD"] = df["DD"].astype(int)
        
        # Filter by date range
        df_filtered = df[df.apply(lambda row: f"{int(row.YY)} {int(row.MM):02d} {int(row.DD):02d}" in date_range, axis=1)]
        
        # Add station_id, latitude, and longitude columns
        df_filtered["station_id"] = station_id
        df_filtered["latitude"], df_filtered["longitude"] = station_coords.get(station_id, (None, None))
        
        # Append to list
        all_data.append(df_filtered)
    else:
        print(f"Failed to download data for station {station_id}")

# Concatenate all data into a single DataFrame
final_df = pd.concat(all_data, ignore_index=True)

# Save to CSV
final_df.to_csv("all_stations_october_2012.csv", index=False)
print("Saved all_stations_october_2012.csv")
