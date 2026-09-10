"""
Dominick's helpers -- functions to help download and process dominick's data

The notebook provided in the training showcases various things -- however if you want to operationalize 
experiments a little more, it often helps to shift exploration code into functions in separate scripts. 
This script contains helper functions that allow the automated downloading and storing of the data 
in parquet (a very efficient data format for storage and reading/writing). 

"""

import pandas as pd
import numpy as np

def download_category(category_name, path="../data/raw/"):
    """
    Basic function to download raw UPC and movement data for a given category
    """
    url = "https://www.chicagobooth.edu/research/kilts/research-data/-/media/enterprise/centers/kilts/datasets/dominicks-dataset/"
    product_url = f"{url}upc_csv-files/upc{category_name}.csv"
    upc_url = f"{url}movement_csv-files/w{category_name}.zip"

    # Get upc data
    print(f"Downloading product data for {category_name}...")
    df = pd.read_csv(product_url, encoding='latin1')
    df.to_parquet(f"{path}{category_name}_products.parquet", index=False)

    # Get movement data
    print(f"Downloading movement data for {category_name}...")
    df = pd.read_csv(upc_url, encoding='latin1', compression='zip')
    df = df.drop(columns=['PRICE_HEX', 'PROFIT_HEX'])
    df.to_parquet(f"{path}{category_name}_movement.parquet", index=False)
    
    print("Done! Raw data for {category_name} has been downloaded and saved to {path} as parquet files.")

def download_weeks_and_stores(path="../data/raw/"):
    """
    Download the weeks and stores data from URL on the dff repo
    """
    weeks_url = "https://raw.githubusercontent.com/eurostat/dff/master/CSV/weeks.csv"
    stores_url = "https://raw.githubusercontent.com/eurostat/dff/master/CSV/stores.csv"

    # Get and store store data
    print('Downloading store data...')
    df_stores = pd.read_csv(stores_url, header=None, names=['STORE','CITY','PRICE_TIER','ZONE','ZIP_CODE','ADDRESS'])
    df_stores.to_parquet(f"{path}stores.parquet", index=False)

    # Get and store week data
    print('Downloading week data...')
    df_weeks = pd.read_csv(weeks_url, header=None, names=['WEEK','START','END','SPECIAL_EVENTS'])
    # 1. Convert to datetime formats
    df_weeks['START'] = pd.to_datetime(df_weeks['START'], format='%m/%d/%y')
    df_weeks['END'] = pd.to_datetime(df_weeks['END'], format='%m/%d/%y')
    # 2. Create the reference period as a string (YYYY-MM)
    df_weeks['REF_PERIOD'] = df_weeks['START'].dt.strftime('%Y-%m')
    # 3. Check if the week is fully in the month
    # np.where acts like ifelse(): if months match, return True, otherwise return NaN
    df_weeks['WEEK_FULLY_IN_MONTH'] = np.where(
        df_weeks['START'].dt.month == df_weeks['END'].dt.month, 
        True, 
        np.nan
    )
    # 4. Group by REF_PERIOD and calculate the week of the month
    # We count the non-NaN values cumulatively, then apply .where() to put NaNs back 
    # in the rows that originally straddled months.
    valid_weeks = df_weeks['WEEK_FULLY_IN_MONTH'].notna()
    df_weeks['WEEK_OF_MONTH'] = (
        valid_weeks
        .groupby(df_weeks['REF_PERIOD'])
        .cumsum()
        .where(valid_weeks, np.nan)
    )
    df_weeks.to_parquet(f"{path}weeks.parquet", index=False)
    

if __name__ == "__main__":
    # Example of reading in a CSV file with pandas
    download_weeks_and_stores(path="data/raw/")

    # download_category("lnd", path="data/ralw/")
    download_category("gro", path="data/raw/")
    # download_category("ber", path="data/raw/")
