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

df['datetime'] = pd.to_datetime(df[['YY', 'MM', 'DD', 'hh', 'mm']].rename(columns={'YY': 'year', 'MM': 'month', 'DD': 'day', 'hh': 'hour', 'mm': 'minute'}))

valid_wvht = df[df['WVHT'] != 99.0]['WVHT']
threshold = valid_wvht.quantile(0.95)

significant_storms = df[df['WVHT'] > threshold][['datetime', 'WVHT']]
significant_storms = significant_storms.groupby(significant_storms['datetime'].dt.date).agg({'WVHT': 'max'}).reset_index()

print(f"Significant storm threshold (95th percentile): {threshold:.2f} meters")
print(f"Number of significant storm days: {len(significant_storms)}")
print("\nTop 10 significant storms by max wave height:")
print(significant_storms.sort_values('WVHT', ascending=False).head(10))