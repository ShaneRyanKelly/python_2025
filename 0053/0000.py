import requests
import gzip
import io
import pandas as pd

# Base URL for NOAA data
data_url = "https://www.ndbc.noaa.gov/view_text_file.php?filename=44025h{year}.txt.gz&dir=data/historical/stdmet/"
years = range(2019, 2025)  # From 2019 to 2024

# Column names based on the provided data
columns = [
    "YY", "MM", "DD", "hh", "mm", "WDIR", "WSPD", "GST", "WVHT", "DPD", "APD", "MWD", "PRES", "ATMP", "WTMP", "DEWP", "VIS", "TIDE"
]

# List to store data
data_frames = []

for year in years:
    url = data_url.format(year=year)
    print(f"Downloading: {url}")
    
    response = requests.get(url)
    if response.status_code == 200:
        with gzip.open(io.BytesIO(response.content), 'rt') as f:
            lines = f.readlines()
            
        # Find the first line of actual data (skip header lines starting with #)
        data_lines = [line.strip() for line in lines if not line.startswith("#")]
        
        # Read into DataFrame
        df = pd.read_csv(io.StringIO("\n".join(data_lines)), delim_whitespace=True, names=columns, dtype=str)
        df.insert(0, "Year", str(year))  # Ensure year is explicitly included
        data_frames.append(df)
    else:
        print(f"Failed to download data for {year}")

# Concatenate all data
if data_frames:
    final_df = pd.concat(data_frames, ignore_index=True)
    final_df.to_csv("noaa_44025_2019_2024.csv", index=False)
    print("CSV file saved: noaa_44025_2019_2024.csv")
else:
    print("No data downloaded.")
