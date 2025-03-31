# Import required libraries
import pandas as pd
import matplotlib.pyplot as plt

# Load and prepare the data
filename = 'all_stations_october_2012.csv'
df = pd.read_csv(filename)

# Create datetime column and filter date range
df['datetime'] = pd.to_datetime(df[['YY', 'MM', 'DD', 'hh', 'mm']].rename(
    columns={'YY': 'year', 'MM': 'month', 'DD': 'day', 'hh': 'hour', 'mm': 'minute'}))
df_filtered = df[df['datetime'].between('2012-10-22', '2012-10-30 23:59:59')]

# Clean outlier values and calculate storm intensity
df_filtered = df_filtered.replace([99.0, 999.0, 9999.0], pd.NA)
df_filtered = df_filtered.interpolate()
df_filtered['storm_intensity'] = df_filtered['WSPD'] * df_filtered['WVHT']
df_filtered = df_filtered.dropna(subset=['storm_intensity', 'WVHT', 'WSPD'])
df_filtered[['WSPD', 'WVHT', 'storm_intensity']] = df_filtered[['WSPD', 'WVHT', 'storm_intensity']].apply(pd.to_numeric)

# Find maximum intensity at station 44009
df_44009 = df_filtered[df_filtered['station_id'] == 44009]
max_intensity_44009 = df_44009.loc[df_44009['storm_intensity'].idxmax()]
max_intensity_date = max_intensity_44009['datetime']

# Select key dates for visualization
selected_dates = [
    pd.Timestamp('2012-10-22 12:00:00'),
    pd.Timestamp('2012-10-26 12:00:00'),
    max_intensity_date,
    pd.Timestamp('2012-10-30 12:00:00')
]

# Prepare data for each selected date
date_data = {}
for date in selected_dates:
    date_df = df_filtered[df_filtered['datetime'].dt.date == date.date()]
    date_df = date_df.groupby(['station_id', 'latitude', 'longitude']).agg({
        'WSPD': 'mean',
        'WVHT': 'mean',
        'storm_intensity': 'mean'
    }).reset_index()
    date_data[date.strftime('%Y-%m-%d')] = date_df

# Create 4 bubble charts for storm development
try:
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
    
    # Create category 5 projection visualization for max intensity date
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
    
    plt.show()
except Exception as e:
    print(f"Error generating visualizations: {e}")