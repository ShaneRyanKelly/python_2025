import pandas as pd

filename = 'noaa_44025_2019_2024.csv'
df = pd.read_csv(filename)

print("=== DATA OVERVIEW ===")
print(f"Rows: {df.shape[0]}, Columns: {df.shape[1]}")
print("\nFirst 5 rows:")
print(df.head())

print("\nColumn names:")
print(df.columns.tolist())

print("\nData types:")
print(df.dtypes)

print("\nMissing values:")
print(df.isnull().sum())

print("\nSummary statistics:")
print(df.describe(include='all').transpose())

print(f"\nDuplicate rows: {df.duplicated().sum()}")

# Replace invalid values (99.0, 999.0, etc.) with NaN
import numpy as np
df['WVHT'] = df['WVHT'].replace(99.0, np.nan)
df['WSPD'] = df['WSPD'].replace(99.0, np.nan)
df['GST'] = df['GST'].replace(99.0, np.nan)

# Create a datetime column by combining YY, MM, DD, hh, mm
df['datetime'] = pd.to_datetime(df[['YY', 'MM', 'DD', 'hh', 'mm']].rename(columns={'YY': 'year', 'MM': 'month', 'DD': 'day', 'hh': 'hour', 'mm': 'minute'}))

# Drop rows with missing WVHT values
df_clean = df.dropna(subset=['WVHT'])

# Define significant storms as those with wave height above the 95th percentile
wave_height_threshold = df_clean['WVHT'].quantile(0.95)
significant_storms = df_clean[df_clean['WVHT'] >= wave_height_threshold]

# Group by date to find max wave height per day
significant_storms_daily = significant_storms.groupby(significant_storms['datetime'].dt.date)['WVHT'].max().reset_index()
significant_storms_daily.columns = ['date', 'max_wave_height']

print(f"Wave height threshold for significant storms (95th percentile): {wave_height_threshold:.2f} meters")
print(f"Number of significant storm days: {len(significant_storms_daily)}")
print("\nFirst 5 significant storm days:")
print(significant_storms_daily.head())

import matplotlib.pyplot as plt

# Ensure date is in datetime format
significant_storms_daily['date'] = pd.to_datetime(significant_storms_daily['date'])

# Create the plot
plt.figure(figsize=(12, 6))
plt.plot(significant_storms_daily['date'], significant_storms_daily['max_wave_height'], 
         linestyle='-', color='blue', label='Max Wave Height')
plt.axhline(y=wave_height_threshold, color='red', linestyle='--', 
            label=f'Threshold ({wave_height_threshold:.2f} m)')

# Customize the plot
plt.title('Significant Storm Systems (2019-2024) by Date and Max Wave Height', fontsize=14)
plt.xlabel('Date', fontsize=12)
plt.ylabel('Maximum Wave Height (meters)', fontsize=12)
plt.legend()
plt.grid(True, linestyle='--', alpha=0.7)

# Rotate x-axis labels for better readability
plt.xticks(rotation=45)

# Adjust layout to prevent label cutoff
plt.tight_layout()

# Display the plot
plt.show()

# Extract month from significant storm dates
significant_storms_daily['month'] = significant_storms_daily['date'].dt.month

# Calculate average number of significant storms per month across all years
storms_per_month = significant_storms_daily.groupby('month').size()
years_covered = significant_storms_daily['date'].dt.year.nunique()
avg_storms_per_month = storms_per_month / years_covered

# Create a forecast for 2025
forecast_2025 = pd.DataFrame({
    'month': range(1, 13),
    'predicted_storms': avg_storms_per_month.values
})

# Round to nearest integer for practical interpretation
forecast_2025['predicted_storms'] = forecast_2025['predicted_storms'].round().astype(int)

print("Average significant storms per month (2019-2024):")
print(avg_storms_per_month)
print("\nStorm forecast for 2025 (number of significant storm days per month):")
print(forecast_2025)

# Load the data
filename = 'noaa_44025_2019_2024.csv'
try:
    df = pd.read_csv(filename)
except FileNotFoundError:
    print(f"Error: File '{filename}' not found.")
    exit()

# Replace invalid values with NaN
df['WVHT'] = df['WVHT'].replace(99.0, np.nan)

# Create datetime column
df['datetime'] = pd.to_datetime(df[['YY', 'MM', 'DD', 'hh', 'mm']].rename(
    columns={'YY': 'year', 'MM': 'month', 'DD': 'day', 'hh': 'hour', 'mm': 'minute'}))

# Drop rows with missing wave height
df_clean = df.dropna(subset=['WVHT'])

# Define significant storms (wave height >= 95th percentile)
wave_height_threshold = df_clean['WVHT'].quantile(0.95)
significant_storms = df_clean[df_clean['WVHT'] >= wave_height_threshold]

# Group by date to find max wave height per day
significant_storms_daily = significant_storms.groupby(significant_storms['datetime'].dt.date)['WVHT'].max().reset_index()
significant_storms_daily.columns = ['date', 'max_wave_height']
significant_storms_daily['date'] = pd.to_datetime(significant_storms_daily['date'])

# Generate visualization
plt.figure(figsize=(12, 6))
plt.plot(significant_storms_daily['date'], significant_storms_daily['max_wave_height'], 
         linestyle='-', color='blue', label='Max Wave Height')
plt.axhline(y=wave_height_threshold, color='red', linestyle='--', 
            label=f'Threshold ({wave_height_threshold:.2f} m)')
plt.title('Significant Storm Systems (2019-2024) by Date and Max Wave Height', fontsize=14)
plt.xlabel('Date', fontsize=12)
plt.ylabel('Maximum Wave Height (meters)', fontsize=12)
plt.legend()
plt.grid(True, linestyle='--', alpha=0.7)
plt.xticks(rotation=45)
plt.tight_layout()
plt.show()