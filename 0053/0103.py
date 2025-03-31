import pandas as pd
filename = 'meteorological_oceanographic_data.csv'
if filename.endswith('.csv'): 
    df = pd.read_csv(filename)
elif filename.endswith(('.xlsx', '.xls')): 
    df = pd.read_excel(filename)
elif filename.endswith('.json'): 
    df = pd.read_json(filename)
elif filename.endswith('.txt'): 
    df = pd.read_csv(filename, sep=None, engine='python')
else: 
    print(f"File type not recognized. Attempting to load as CSV.")
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

print("\nDate range:")
if 'date' in df.columns:
    df['date'] = pd.to_datetime(df['date'])
    print(f"Min date: {df['date'].min()}")
    print(f"Max date: {df['date'].max()}")
else:
    print("No 'date' column found. Looking for potential date columns:")
    date_cols = df.select_dtypes(include=['datetime64', 'object']).columns
    print(date_cols)
    if 'Year' in df.columns:
        print(f"Min year: {df['Year'].min()}")
        print(f"Max year: {df['Year'].max()}")
        if 'Month' in df.columns:
            print(f"First Month in {df['Year'].min()}: {df.loc[df['Year'] == df['Year'].min(), 'Month'].min()}")
            print(f"Last Month in {df['Year'].max()}: {df.loc[df['Year'] == df['Year'].max(), 'Month'].max()}")
        else:
            print("No 'Month' column found.")

df['datetime'] = pd.to_datetime(
    df[['Year', 'MM', 'DD', 'hh', 'mm']].rename(
        columns={'Year': 'year', 'MM': 'month', 'DD': 'day', 'hh': 'hour', 'mm': 'minute'}
    )
)

print("Date range after datetime creation:")
print(f"Min datetime: {df['datetime'].min()}")
print(f"Max datetime: {df['datetime'].max()}")

print("\n2024 data coverage:")
df_2024 = df[df['Year'] == 2024]
print(f"First datetime in 2024: {df_2024['datetime'].min()}")
print(f"Last datetime in 2024: {df_2024['datetime'].max()}")
print(f"Months present in 2024: {sorted(df_2024['MM'].unique())}")

print("\nWave height (WVHT) value distribution:")
print(df['WVHT'].value_counts().sort_index())
print("\nPercentage of WVHT values = 99.0: ", (df['WVHT'] == 99.0).mean() * 100)

df_valid = df[df['WVHT'] != 99.0]
print("\nDate range for valid WVHT data:")
print(f"Min datetime (valid WVHT): {df_valid['datetime'].min()}")
print(f"Max datetime (valid WVHT): {df_valid['datetime'].max()}")