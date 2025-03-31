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

df_valid['month'] = df_valid['datetime'].dt.month
df_valid['year'] = df_valid['datetime'].dt.year

monthly_wvht = df_valid.groupby(['year', 'month'])['WVHT'].mean().reset_index()
monthly_wvht['date'] = pd.to_datetime(monthly_wvht[['year', 'month']].assign(day=1))

print("Monthly WVHT means (first 12 and last 12 rows):")
print(monthly_wvht.head(12))
print(monthly_wvht.tail(12))

print("\nAverage WVHT by month across all years:")
monthly_avg = monthly_wvht.groupby('month')['WVHT'].mean()
print(monthly_avg)

print("\nChecking for seasonal patterns:")
monthly_wvht['month_only'] = monthly_wvht['date'].dt.month
seasonal_pivot = monthly_wvht.pivot(index='year', columns='month_only', values='WVHT')
print("\nSeasonal pivot table (WVHT by year and month):")
print(seasonal_pivot)

historical_monthly = monthly_wvht[monthly_wvht['year'] < 2024]
historical_means = historical_monthly.groupby('month')['WVHT'].mean()

missing_months = pd.DataFrame({
    'year': [2024] * 3,
    'month': [10, 11, 12],
    'WVHT': [historical_means.loc[10], historical_means.loc[11], historical_means.loc[12]]
})
missing_months['date'] = pd.to_datetime(missing_months[['year', 'month']].assign(day=1))

print("Historical monthly means (2019-2023):")
print(historical_means)

print("\nPredicted WVHT for missing 2024 months (Oct-Dec):")
print(missing_months)

complete_2024 = pd.concat([
    monthly_wvht[monthly_wvht['year'] == 2024],
    missing_months
]).sort_values('date')

print("\nComplete 2024 monthly WVHT (observed and predicted):")
print(complete_2024[['date', 'WVHT']])