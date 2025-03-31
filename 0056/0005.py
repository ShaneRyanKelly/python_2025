import pandas as pd

filename = 'all_stations_october_2012.csv'
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

df['datetime'] = pd.to_datetime(df[['YY', 'MM', 'DD', 'hh', 'mm']].rename(
    columns={'YY': 'year', 'MM': 'month', 'DD': 'day', 'hh': 'hour', 'mm': 'minute'}))

df_filtered = df[df['datetime'].between('2012-10-22', '2012-10-30 23:59:59')]

df_filtered = df_filtered.replace([99.0, 999.0, 9999.0], pd.NA)

df_filtered = df_filtered.interpolate()

df_filtered['storm_intensity'] = df_filtered['WSPD'] * df_filtered['WVHT']

df_filtered = df_filtered.dropna(subset=['storm_intensity', 'WVHT', 'WSPD'])
df_filtered[['WSPD', 'WVHT', 'storm_intensity']] = df_filtered[['WSPD', 'WVHT', 'storm_intensity']].apply(pd.to_numeric)

print("Filtered date range:", df_filtered['datetime'].min(), "to", df_filtered['datetime'].max())
print("\nCleaned data summary:")
print(df_filtered[['WVHT', 'storm_intensity', 'WSPD']].describe())
print("\nStation 44009 presence:", 44009 in df_filtered['station_id'].values)
print("\nNumber of unique stations:", df_filtered['station_id'].nunique())
print("\nUnique stations:", df_filtered['station_id'].unique())

df_44009 = df_filtered[df_filtered['station_id'] == 44009]
max_intensity_44009 = df_44009.loc[df_44009['storm_intensity'].idxmax()]
max_intensity_date = max_intensity_44009['datetime']

selected_dates = [
    pd.Timestamp('2012-10-22 12:00:00'),
    pd.Timestamp('2012-10-26 12:00:00'),
    max_intensity_date,
    pd.Timestamp('2012-10-30 12:00:00')
]

date_data = {}
for date in selected_dates:
    date_df = df_filtered[df_filtered['datetime'].dt.date == date.date()]
    date_df = date_df.groupby(['station_id', 'latitude', 'longitude']).agg({
        'WSPD': 'mean',
        'WVHT': 'mean',
        'storm_intensity': 'mean'
    }).reset_index()
    date_data[date.strftime('%Y-%m-%d')] = date_df

print("Selected dates for visualization:")
for date in date_data.keys():
    print(f"\nDate: {date}")
    print(date_data[date][['station_id', 'WSPD', 'WVHT', 'storm_intensity']])
print("\nMaximum intensity at 44009:")
print(max_intensity_44009[['datetime', 'WSPD', 'WVHT', 'storm_intensity']])

from sklearn.linear_model import LinearRegression
import numpy as np

X = df_filtered[['WSPD']].values
y = df_filtered['WVHT'].values

model = LinearRegression()
model.fit(X, y)

cat5_wspd = np.array([70]).reshape(-1, 1)

predicted_wvht = model.predict(cat5_wspd)

print(f"Predicted WVHT (Cat 5): {predicted_wvht}")

max_intensity_date_str = max_intensity_date.strftime('%Y-%m-%d')
max_intensity_df = date_data[max_intensity_date_str].copy()

max_intensity_df['cat5_WSPD'] = cat5_wspd[0, 0]
max_intensity_df['cat5_storm_intensity'] = cat5_wspd[0, 0] * predicted_wvht[0]

visualization_data = {
    'bubble_charts': date_data,
    'max_intensity_cat5': max_intensity_df
}

print("Category 5 projection for maximum intensity date:")
print(max_intensity_df[['station_id', 'WSPD', 'cat5_WSPD', 'WVHT', 
                       'storm_intensity', 'cat5_storm_intensity']])

import matplotlib.pyplot as plt

fig, axes = plt.subplots(2, 2, figsize=(15, 10))
axes = axes.ravel()

for idx, (date, data) in enumerate(visualization_data['bubble_charts'].items()):
    ax = axes[idx]
    scatter = ax.scatter(data['longitude'], data['latitude'], 
                        s=data['storm_intensity']*10, 
                        alpha=0.5)
    ax.set_title(f'Storm Intensity - {date}')
    ax.set_xlabel('Longitude')
    ax.set_ylabel('Latitude')
    for i, station in enumerate(data['station_id']):
        ax.annotate(station, (data['longitude'].iloc[i], 
                            data['latitude'].iloc[i]))
plt.tight_layout()

plt.show()

from matplotlib.lines import Line2D

plt.figure(figsize=(10, 8))
max_data = visualization_data['max_intensity_cat5']
actual = plt.scatter(max_data['longitude'], max_data['latitude'],
                    s=max_data['storm_intensity']*10, 
                    alpha=0.5, label='Actual Intensity', c='blue')
cat5 = plt.scatter(max_data['longitude'], max_data['latitude'],
                  s=max_data['cat5_storm_intensity']*10, 
                  alpha=0.3, label='Cat 5 Projection', c='red')
plt.title(f'Maximum Intensity at 44009 with Cat 5 Projection - {max_intensity_date_str}')
plt.xlabel('Longitude')
plt.ylabel('Latitude')
for i, station in enumerate(max_data['station_id']):
    plt.annotate(station, (max_data['longitude'].iloc[i], 
                          max_data['latitude'].iloc[i]))

legend_elements = [
    Line2D([0], [0], marker='o', color='w', markerfacecolor='blue', markersize=10, label='Actual Intensity'),
    Line2D([0], [0], marker='o', color='w', markerfacecolor='red', markersize=10, label='Cat 5 Projection')
]

plt.legend(handles=legend_elements, loc='upper left', bbox_to_anchor=(1, 1), ncol=1)

plt.tight_layout()

plt.show()

print("Visualization code prepared.")
print("The code generates:")
print("- 4 bubble charts for selected dates showing storm intensity")
print("- 1 special chart showing actual vs category 5 projection for maximum intensity at 44009")
print("Bubble sizes are scaled by storm intensity (WSPD * WVHT)")
print("Latitude on y-axis, longitude on x-axis")
print("Station IDs are annotated on each bubble")

import pandas as pd
import matplotlib.pyplot as plt
from sklearn.linear_model import LinearRegression
import numpy as np
from matplotlib.lines import Line2D

# Load and prepare data
try:
    filename = 'all_stations_october_2012.csv'
    df = pd.read_csv(filename)
except FileNotFoundError:
    print("Error: File not found. Please ensure the file path is correct.")
    exit()

# Create datetime column and filter date range
df['datetime'] = pd.to_datetime(df[['YY', 'MM', 'DD', 'hh', 'mm']].rename(
    columns={'YY': 'year', 'MM': 'month', 'DD': 'day', 'hh': 'hour', 'mm': 'minute'}))
df_filtered = df[df['datetime'].between('2012-10-22', '2012-10-30 23:59:59')]

# Clean outlier values and calculate storm intensity
df_filtered = df_filtered.replace([99.0, 999.0, 9999.0], pd.NA)
df_filtered = df_filtered.interpolate()
df_filtered['storm_intensity'] = df_filtered['WSPD'] * df_filtered['WVHT']
df_filtered = df_filtered.dropna(subset=['storm_intensity', 'WVHT', 'WSPD'])
df_filtered[['WSPD', 'WVHT', 'storm_intensity']] = df_filtered[['WSPD', 'WVHT', 'storm_intensity']].apply(pd.to_numeric)

# Find maximum intensity at 44009 and select key dates
df_44009 = df_filtered[df_filtered['station_id'] == 44009]
max_intensity_44009 = df_44009.loc[df_44009['storm_intensity'].idxmax()]
max_intensity_date = max_intensity_44009['datetime']

selected_dates = [
    pd.Timestamp('2012-10-22 12:00:00'),
    pd.Timestamp('2012-10-26 12:00:00'),
    max_intensity_date,
    pd.Timestamp('2012-10-30 12:00:00')
]

# Prepare data for each selected date
date_data = {}
for date in selected_dates:
    date_df = df_filtered[df_filtered['datetime'].dt.date == date.date()]
    date_df = date_df.groupby(['station_id', 'latitude', 'longitude']).agg({
        'WSPD': 'mean',
        'WVHT': 'mean',
        'storm_intensity': 'mean'
    }).reset_index()
    date_data[date.strftime('%Y-%m-%d')] = date_df

# Calculate category 5 projection
X = df_filtered[['WSPD']].values
y = df_filtered['WVHT'].values
model = LinearRegression()
model.fit(X, y)
cat5_wspd = np.array([70]).reshape(-1, 1)
predicted_wvht = model.predict(cat5_wspd)

max_intensity_date_str = max_intensity_date.strftime('%Y-%m-%d')
max_intensity_df = date_data[max_intensity_date_str].copy()
max_intensity_df['cat5_WSPD'] = cat5_wspd[0, 0]
max_intensity_df['cat5_storm_intensity'] = cat5_wspd[0, 0] * predicted_wvht[0]

visualization_data = {
    'bubble_charts': date_data,
    'max_intensity_cat5': max_intensity_df
}

# Create 4 bubble charts
fig, axes = plt.subplots(2, 2, figsize=(15, 10))
axes = axes.ravel()

for idx, (date, data) in enumerate(visualization_data['bubble_charts'].items()):
    ax = axes[idx]
    scatter = ax.scatter(data['longitude'], data['latitude'], 
                        s=data['storm_intensity']*10, 
                        alpha=0.5)
    ax.set_title(f'Storm Intensity - {date}')
    ax.set_xlabel('Longitude')
    ax.set_ylabel('Latitude')
    for i, station in enumerate(data['station_id']):
        ax.annotate(station, (data['longitude'].iloc[i], 
                            data['latitude'].iloc[i]))
plt.tight_layout()
plt.show()

# Create category 5 projection chart
plt.figure(figsize=(10, 8))
max_data = visualization_data['max_intensity_cat5']
actual = plt.scatter(max_data['longitude'], max_data['latitude'],
                    s=max_data['storm_intensity']*10, 
                    alpha=0.5, label='Actual Intensity', c='blue')
cat5 = plt.scatter(max_data['longitude'], max_data['latitude'],
                  s=max_data['cat5_storm_intensity']*10, 
                  alpha=0.3, label='Cat 5 Projection', c='red')
plt.title(f'Maximum Intensity at 44009 with Cat 5 Projection - {max_intensity_date_str}')
plt.xlabel('Longitude')
plt.ylabel('Latitude')
for i, station in enumerate(max_data['station_id']):
    plt.annotate(station, (max_data['longitude'].iloc[i], 
                          max_data['latitude'].iloc[i]))

legend_elements = [
    Line2D([0], [0], marker='o', color='w', markerfacecolor='blue', markersize=10, label='Actual Intensity'),
    Line2D([0], [0], marker='o', color='w', markerfacecolor='red', markersize=10, label='Cat 5 Projection')
]

plt.legend(handles=legend_elements, loc='upper left', bbox_to_anchor=(1, 1), ncol=1)
plt.tight_layout()
plt.show()