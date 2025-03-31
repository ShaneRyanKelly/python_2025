import pandas as pd

filename = 'meteorological_oceanographic_data.csv'
if filename.endswith('.csv'): df = pd.read_csv(filename) 
elif filename.endswith(('.xlsx', '.xls')): df = pd.read_excel(filename) 
elif filename.endswith('.json'): df = pd.read_json(filename) 
elif filename.endswith('.txt'): df = pd.read_csv(filename, sep=None, engine='python') 
else: print(f"File type not recognized. Attempting to load as CSV.") 
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