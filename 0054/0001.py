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