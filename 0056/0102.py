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

station_44009 = df_filtered[df_filtered['station_id'] == 44009]
max_intensity_44009 = station_44009.loc[station_44009['storm_intensity'].idxmax()]
max_intensity_date = max_intensity_44009['datetime']

key_dates = [
    pd.Timestamp('2012-10-22 12:00:00'),
    pd.Timestamp('2012-10-26 12:00:00'),
    max_intensity_date,
    pd.Timestamp('2012-10-30 12:00:00')
]

data_for_dates = {}
for date in key_dates:
    closest_data = df_filtered.iloc[df_filtered['datetime'].sub(date).abs().argsort()[:df_filtered['station_id'].nunique()]]
    data_for_dates[date] = closest_data

print("Selected key dates for visualization:")
for date in key_dates:
    print(f"- {date}")
    print(data_for_dates[date][['station_id', 'storm_intensity', 'latitude', 'longitude']].sort_values('station_id'))
    print()

max_intensity_details = max_intensity_44009[['datetime', 'storm_intensity', 'WSPD', 'WVHT', 'latitude', 'longitude']]
print("\nMaximum intensity at station 44009:")
print(max_intensity_details)