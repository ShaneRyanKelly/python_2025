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

import matplotlib.pyplot as plt

fig, axes = plt.subplots(2, 2, figsize=(15, 10))
axes = axes.ravel()

for idx, (date, data) in enumerate(date_data.items()):
    ax = axes[idx]
    scatter = ax.scatter(data['longitude'], data['latitude'], 
                        s=data['storm_intensity']*10, alpha=0.5)
    ax.set_title(f'Storm Intensity - {date}')
    ax.set_xlabel('Longitude')
    ax.set_ylabel('Latitude')
    for i, station in enumerate(data['station_id']):
        ax.annotate(station, (data['longitude'].iloc[i], data['latitude'].iloc[i]))
plt.tight_layout()

plt.show()

fig_cat5 = plt.figure(figsize=(8, 6))
max_date_data = date_data['2012-10-29']
cat5_data = max_date_data.copy()
cat5_data.loc[cat5_data['station_id'] == 44009, 'WSPD'] = 70
cat5_data.loc[cat5_data['station_id'] == 44009, 'storm_intensity'] = 70 * cat5_data.loc[cat5_data['station_id'] == 44009, 'WVHT']

plt.scatter(max_date_data['longitude'], max_date_data['latitude'],
           s=max_date_data['storm_intensity']*10, alpha=0.5, label='Actual')
plt.scatter(cat5_data['longitude'], cat5_data['latitude'],
           s=cat5_data['storm_intensity']*10, alpha=0.3, label='Cat 5 Projection')
plt.title('Max Intensity at 44009 (2012-10-29) - Actual vs Cat 5')
plt.xlabel('Longitude')
plt.ylabel('Latitude')
for i, station in enumerate(max_date_data['station_id']):
    plt.annotate(station, (max_date_data['longitude'].iloc[i], 
                         max_date_data['latitude'].iloc[i]))
plt.legend()
plt.tight_layout()

print("Visualization code prepared. Run in an IDE to view the plots.")
print("First figure shows 4 bubble charts for storm development.")
print("Second figure shows actual vs category 5 projection for max intensity date.")
plt.show()