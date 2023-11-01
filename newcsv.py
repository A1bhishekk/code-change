import pandas as pd

# Load the original CSV file
original_csv_file = 'all_c_cpp_release2.0.csv'
data = pd.read_csv(original_csv_file)

# Select the first 10 rows
first_10_rows = data.head(10)

# Save the first 10 rows to a new CSV file
new_csv_file = 'first_10_rows.csv'
first_10_rows.to_csv(new_csv_file, index=False)

print(f"Saved the first 10 rows to {new_csv_file}")
