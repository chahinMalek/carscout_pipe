import pandas as pd

if __name__ == '__main__':
    df = pd.read_parquet("data/vehicles/e7a3c5e1-ea9d-4101-ab90-fad63a4be6ed")
    print(df.head())
