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

storm_overviews = []
for idx, storm in top_5_storms.iterrows():
    storm_data = df[(df['datetime'] >= storm['start_time']) & (df['datetime'] <= storm['end_time'])]
    overview = {
        'Storm ID': storm['storm_group'],
        'Start Time': storm['start_time'],
        'End Time': storm['end_time'],
        'Duration (hours)': (storm['end_time'] - storm['start_time']).total_seconds() / 3600,
        'Max Wind Speed (m/s)': storm['max_wspd'],
        'Wind Speed Range (m/s)': [storm_data['WSPD'].min(), storm_data['WSPD'].max()],
        'Mean Wind Speed (m/s)': storm_data['WSPD'].mean(),
        'Max Wave Height (m)': storm['max_wvht'],
        'Wave Height Range (m)': [storm_data['WVHT'].min(), storm_data['WVHT'].max()],
        'Mean Wave Height (m)': storm_data['WVHT'].mean()
    }
    storm_overviews.append(overview)

print("\nOverview of Top 5 Storm Systems:")
for overview in storm_overviews:
    print(f"\nStorm ID: {overview['Storm ID']}")
    print(f"Time Period: {overview['Start Time']} to {overview['End Time']}")
    print(f"Duration: {overview['Duration (hours)']:.2f} hours")
    print(f"Wind Speed: Max = {overview['Max Wind Speed (m/s)']:.2f} m/s, "
          f"Range = {overview['Wind Speed Range (m/s)']}, Mean = {overview['Mean Wind Speed (m/s)']:.2f} m/s")
    print(f"Wave Height: Max = {overview['Max Wave Height (m)']:.2f} m, "
          f"Range = {overview['Wave Height Range (m)']}, Mean = {overview['Mean Wave Height (m)']:.2f} m")
    
import matplotlib.pyplot as plt

storm_dates = [storm['Start Time'].date() for storm in storm_overviews]
wspd_values = [storm['Mean Wind Speed (m/s)'] for storm in storm_overviews]
wvht_values = [storm['Mean Wave Height (m)'] for storm in storm_overviews]

x = np.arange(len(storm_dates))
width = 0.4

fig, ax1 = plt.subplots(figsize=(12, 6))

ax2 = ax1.twinx()

ax1.bar(x - width/2, wspd_values, width, label='Mean Wind Speed (m/s)', color='b', alpha=0.7)
ax2.bar(x + width/2, wvht_values, width, label='Mean Wave Height (m)', color='r', alpha=0.7)

ax1.set_xticks(x)
ax1.set_xticklabels(storm_dates, rotation=45)
ax1.set_xlabel('Storm Date')

ax1.set_ylabel('Wind Speed (m/s)', color='b')
ax2.set_ylabel('Wave Height (m)', color='r')

ax1.legend(loc='upper left')
ax2.legend(loc='upper right')

plt.title('Side-by-Side Bar Chart of Wind Speed and Wave Height for Top 5 Storms')
plt.tight_layout()
plt.show()

print("\nVisualization code prepared. Run this code to generate a plot comparing the top 5 storms.")

import matplotlib.pyplot as plt
import numpy as np

bins = [0, 10, 15, 20, 25, 30]  # Wind speed bins up to data max and slightly beyond
labels = ['<10 m/s', '10-15 m/s', '15-20 m/s', '20-25 m/s', '>25 m/s']

df['wind_category'] = pd.cut(df['WSPD'], bins=bins, labels=labels, right=False)

wave_height_by_category = df.groupby('wind_category', observed=True)['WVHT'].mean().reset_index()

plt.figure(figsize=(10, 6))
plt.bar(wave_height_by_category['wind_category'], wave_height_by_category['WVHT'], color='teal', alpha=0.7)
plt.xlabel('Wind Speed Category')
plt.ylabel('Expected Wave Height (m)')
plt.title('Expected Wave Height by Wind Speed Category')
plt.xticks(rotation=45)
plt.tight_layout()
plt.show()

print("\nChart code prepared. Run this code to generate a bar chart of expected wave heights by wind speed category.")
print("Wave height by category data:")
print(wave_height_by_category)