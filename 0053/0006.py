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

historical_avg = monthly_wvht[monthly_wvht['year'] < 2024].groupby('month')['WVHT'].mean()

missing_months = pd.DataFrame({
    'year': [2024] * 6,
    'month': [1, 2, 3, 10, 11, 12],
    'WVHT': [historical_avg.loc[1], historical_avg.loc[2], historical_avg.loc[3], historical_avg.loc[10], historical_avg.loc[11], historical_avg.loc[12]],
    'date': pd.to_datetime(['2024-01-01', '2024-02-01', '2024-03-01', '2024-10-01', '2024-11-01', '2024-12-01'])
})

complete_2024 = pd.concat([monthly_wvht[monthly_wvht['year'] == 2024], missing_months]).sort_values('date')

print("Predicted WVHT for missing 2024 months (Jan-Mar and Oct-Dec):")
print(missing_months[['date', 'WVHT']])

print("\nComplete 2024 monthly WVHT (including predictions):")
print(complete_2024[['date', 'WVHT']])

monthly_by_year = monthly_wvht.pivot(index='month', columns='year', values='WVHT')
monthly_by_year['2024'] = complete_2024.set_index('month')['WVHT']
print("\nData prepared for visualization (WVHT by year and month):")
print(monthly_by_year)

import matplotlib.pyplot as plt

monthly_by_year = monthly_by_year.drop(columns=[2024])  # Remove duplicate 2024 column
monthly_by_year.columns = [str(col) for col in monthly_by_year.columns]

plt.figure(figsize=(12, 6))
colors = ['blue', 'green', 'red', 'purple', 'orange', 'black']
for i, year in enumerate(monthly_by_year.columns):
    plt.plot(monthly_by_year.index, monthly_by_year[year], 
             label=year, color=colors[i], 
             linestyle='--' if year == '2024' else '-',
             alpha=0.7 if year == '2024' else 1)

plt.title('Monthly Wave Height (WVHT) by Year')
plt.xlabel('Month')
plt.ylabel('Wave Height (m)')
plt.grid(True)
plt.legend(title='Year')
plt.xticks(range(1, 13))
plt.tight_layout()
print("Visualization code prepared. Run this code to generate the plot.")

plt.show()