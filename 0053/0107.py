import pandas as pd
import matplotlib.pyplot as plt

# Load the data (replace with your actual filename)
filename = 'meteorological_oceanographic_data.csv'
try:
    df = pd.read_csv(filename)
except Exception as e:
    print(f"Error loading file: {e}")
    raise

# Create datetime column
try:
    df['datetime'] = pd.to_datetime(
        df[['Year', 'MM', 'DD', 'hh', 'mm']].rename(
            columns={'Year': 'year', 'MM': 'month', 'DD': 'day', 'hh': 'hour', 'mm': 'minute'}
        )
    )
except Exception as e:
    print(f"Error creating datetime: {e}")
    raise

# Filter valid WVHT data (excluding 99.0 placeholder)
df_valid = df[df['WVHT'] != 99.0]

# Aggregate to monthly means
df_valid['month'] = df_valid['datetime'].dt.month
df_valid['year'] = df_valid['datetime'].dt.year
monthly_wvht = df_valid.groupby(['year', 'month'])['WVHT'].mean().reset_index()
monthly_wvht['date'] = pd.to_datetime(monthly_wvht[['year', 'month']].assign(day=1))

# Calculate historical monthly averages (2019-2023)
historical_avg = monthly_wvht[monthly_wvht['year'] < 2024].groupby('month')['WVHT'].mean()

# Create predictions for missing 2024 months
missing_months = pd.DataFrame({
    'year': [2024] * 6,
    'month': [1, 2, 3, 10, 11, 12],
    'WVHT': [historical_avg.loc[1], historical_avg.loc[2], historical_avg.loc[3],
             historical_avg.loc[10], historical_avg.loc[11], historical_avg.loc[12]],
    'date': pd.to_datetime(['2024-01-01', '2024-02-01', '2024-03-01',
                          '2024-10-01', '2024-11-01', '2024-12-01'])
})

# Combine observed and predicted 2024 data
complete_2024 = pd.concat([monthly_wvht[monthly_wvht['year'] == 2024], missing_months]).sort_values('date')

# Prepare data for visualization
monthly_by_year = monthly_wvht.pivot(index='month', columns='year', values='WVHT')
monthly_by_year['2024'] = complete_2024.set_index('month')['WVHT']
monthly_by_year.columns = [str(col) for col in monthly_by_year.columns]

# Create visualization
plt.figure(figsize=(12, 6))
colors = ['blue', 'green', 'red', 'purple', 'orange', 'black']
try:
    for i, year in enumerate(monthly_by_year.columns):
        plt.plot(monthly_by_year.index, monthly_by_year[year],
                label=year, color=colors[i],
                linestyle='--' if year == '2024' else '-',
                alpha=0.7 if year == '2024' else 1)
except Exception as e:
    print(f"Error creating plot: {e}")
    raise

plt.title('Monthly Wave Height (WVHT) by Year')
plt.xlabel('Month')
plt.ylabel('Wave Height (m)')
plt.grid(True)
plt.legend(title='Year')
plt.xticks(range(1, 13))
plt.tight_layout()
plt.show()