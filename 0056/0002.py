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