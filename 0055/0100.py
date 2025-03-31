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

# Focus on wind speed (WSPD) and wave height (WVHT)
print("\nMissing values in key columns:")
print(f"WSPD missing: {df['WSPD'].isnull().sum()}")
print(f"WVHT missing: {df['WVHT'].isnull().sum()}")

# Interpolate missing values in WSPD and WVHT
df['WSPD'] = df['WSPD'].interpolate(method='linear')
df['WVHT'] = df['WVHT'].interpolate(method='linear')

# Verify interpolation
print("\nMissing values after interpolation:")
print(f"WSPD missing: {df['WSPD'].isnull().sum()}")
print(f"WVHT missing: {df['WVHT'].isnull().sum()}")

# Save the cleaned dataframe for subsequent steps
df.to_csv('cleaned_noaa_44025_2019_2024.csv', index=False)