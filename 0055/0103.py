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

df['datetime'] = pd.to_datetime(df[['YY', 'MM', 'DD', 'hh', 'mm']].rename(columns={'YY': 'year', 'MM': 'month', 'DD': 'day', 'hh': 'hour', 'mm': 'minute'}))

df.set_index('datetime', inplace=True)

df['WSPD'] = df['WSPD'].replace(99.0, np.nan)
df['WVHT'] = df['WVHT'].replace(99.0, np.nan)

print("\nMissing values after replacing 99.0 with NaN and before interpolation:")
print(df[['WSPD', 'WVHT']].isnull().sum())

df['WSPD'] = df['WSPD'].interpolate(method='time')
df['WVHT'] = df['WVHT'].interpolate(method='time')

print("\nMissing values after interpolation:")
print(df[['WSPD', 'WVHT']].isnull().sum())

print("\nSummary statistics after interpolation:")
print(df[['WSPD', 'WVHT']].describe())

print("\nFirst 5 rows after interpolation:")
print(df[['WSPD', 'WVHT']].head())

storm_threshold_wspd = 15.0
storm_threshold_wvht = 2.0

df['is_storm'] = (df['WSPD'] > storm_threshold_wspd) & (df['WVHT'] > storm_threshold_wvht)

df['storm_group'] = (df['is_storm'] != df['is_storm'].shift()).cumsum()
df.loc[~df['is_storm'], 'storm_group'] = 0

df = df.reset_index()

storm_events = df[df['is_storm']].groupby('storm_group').agg({
    'WSPD': ['max', 'mean'],
    'WVHT': ['max', 'mean'],
    'datetime': ['min', 'max', 'count']
}).reset_index()

storm_events.columns = ['storm_group', 'max_wspd', 'mean_wspd', 'max_wvht', 'mean_wvht', 'start_time', 'end_time', 'duration']

storm_events['intensity_score'] = storm_events['max_wspd'] * storm_events['max_wvht']

top_5_storms = storm_events[storm_events['duration'] > 1].nlargest(5, 'intensity_score')

print("\nTop 5 storm systems by intensity score:")
print(top_5_storms[['start_time', 'end_time', 'max_wspd', 'max_wvht', 'intensity_score', 'duration']])

storm_details = []
for idx, row in top_5_storms.iterrows():
    storm_data = df[(df['datetime'] >= row['start_time']) & (df['datetime'] <= row['end_time'])]
    storm_summary = {
        'Storm_ID': row['storm_group'],
        'Time_Period': f"{row['start_time']} to {row['end_time']}",
        'Duration (hours)': row['duration'] * 10 / 60,  # Convert 10-min intervals to hours
        'Wind_Speed_Range (m/s)': f"{storm_data['WSPD'].min():.2f} - {storm_data['WSPD'].max():.2f}",
        'Wave_Height_Range (m)': f"{storm_data['WVHT'].min():.2f} - {storm_data['WVHT'].max():.2f}",
        'Mean_Wind_Speed (m/s)': storm_data['WSPD'].mean(),
        'Mean_Wave_Height (m)': storm_data['WVHT'].mean()
    }
    storm_details.append(storm_summary)

storm_overview = pd.DataFrame(storm_details)

print("\nOverview of the 5 most significant storm systems:")
print(storm_overview)