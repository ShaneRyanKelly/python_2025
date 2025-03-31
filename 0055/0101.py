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

print("\nFocus on wave height and wind speed columns:")
wave_cols = [col for col in df.columns if 'WVHT' in col or 'wave' in col.lower()]
wind_cols = [col for col in df.columns if 'WSPD' in col or 'wind' in col.lower()]
if wave_cols and wind_cols:
    print(f"Wave height columns: {wave_cols}")
    print(f"Wind speed columns: {wind_cols}")
    print("\nMissing values in wave height columns:")
    print(df[wave_cols].isnull().sum())
    print("\nMissing values in wind speed columns:")
    print(df[wind_cols].isnull().sum())


    print(f"\nWave Height ({df[wave_cols]}) Distribution:")
    print(df[wave_cols].describe())
    print(f"\nWind Speed ({df[wind_cols]}) Distribution:")
    print(df[wind_cols].describe())
else:
    print("\nWave height or wind speed columns not found. Please check column names.")

import numpy as np

df['WSPD'] = df['WSPD'].replace(99.0, np.nan)
df['WVHT'] = df['WVHT'].replace(99.0, np.nan)

print("\nMissing values after replacing 99.0 with NaN:")
print(df[['WSPD', 'WVHT']].isnull().sum())

df['WSPD'] = df['WSPD'].interpolate(method='linear')
df['WVHT'] = df['WVHT'].interpolate(method='linear')

print("\nMissing values after interpolation:")
print(df[['WSPD', 'WVHT']].isnull().sum())

print("\nUpdated summary statistics for WSPD and WVHT:")
print(df[['WSPD', 'WVHT']].describe())