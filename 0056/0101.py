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

df_filtered = df[(df['datetime'] >= '2012-10-22') & (df['datetime'] <= '2012-10-30 23:59:59')]

df_filtered['intensity'] = df_filtered['WSPD'] + df_filtered['WVHT']

print("Filtered date range:", df_filtered['datetime'].min(), "to", df_filtered['datetime'].max())
print("\nFiltered data shape:", df_filtered.shape)
print("\nUnique stations:", df_filtered['station_id'].unique())
print("\nStation 44009 data:")
print(df_filtered[df_filtered['station_id'] == 44009][['datetime', 'WSPD', 'WVHT', 'intensity']].head())