import time
import requests
import pandas as pd
import json
from sqlalchemy import create_engine

# If file exists and no new updates, fetch data from existing file
def fetch_data(*, update: bool = False, json_cache: str):
    if update:
        json_data = None
    else:
        try:
            with open(json_cache, 'r') as f:
                json_data = json.load(f) # Retrieve data from local cache
        except(FileNotFoundError, json.JSONDecodeError) as e:
            json_data = None
    
    # make new api call
    if not json_data:
        json_data = []
        for i in range(len(tickers)):
            url = f'https://www.alphavantage.co/query?function=GLOBAL_QUOTE&symbol={tickers[i]}&apikey={api_key}'
            r = requests.get(url)
            data = r.json()
            json_data.append(data)
        
            # Calculate sleep time to maintain rate limit
            start = time.time()
            elapsed = time.time() - start
            sleep_time = max(0, interval - elapsed)
            time.sleep(sleep_time)
    
        # Store new data in local cache
        with open(json_cache, "w") as f:
            json.dump(json_data, f, indent=4)
    
    return json_data

if __name__ == '__main__':
    api_key = "STNE15X0T16UDA4F"
    tickers = ["IBM", "MSFT", "AAPL", "UBS"]
    calls_per_minute = 75
    interval = 60.0 / calls_per_minute  # Time between calls in seconds
    json_cache = "global_quote_endpoint.json"
    csv_filename = "global_quote_endpoint.csv"
    data = fetch_data(update = True, json_cache = json_cache) # Call function to fetch existing data or make new api call
    # Set update to true if need new data

    # Rename columns to remove numbers (ex. '01. symbol' becomes just 'symbol')
    # split keys and remove if they can be converted to int
    new_data = [] # Create new list to store updated data
    for i in range(len(data)):
        for key, value in data[i].items():
            new_value = {}
            for key1, value1 in value.items():
                parts = key1.split('. ')
                for part in parts:
                    new_value[part] = value1
            keys_to_remove = []
            for key2, value2 in new_value.items():
                try:
                    int(key2)
                    keys_to_remove.append(key2)
                except ValueError:
                    continue
            for j in keys_to_remove:
                del new_value[j]
            new_data.append(new_value)

    # Export data into csv file
    df = pd.DataFrame(new_data)
    df.to_csv(csv_filename)

    # Create another pandas dataframe with just 2 columns (symbol, quantity), default value 1000 for both
    symbol_quantity = []
    symbol_quantity_csv = "symbol_quantity.csv"
    symbol_quantity_dict = {'symbol': '1000', 'quantity': '1000'}
    symbol_quantity.append(symbol_quantity_dict)
    df = pd.DataFrame(symbol_quantity)
    df.to_csv(symbol_quantity_csv)

    # log data to mysql database
    # MySQL database connection details
    DB_USER = 'root'
    DB_PASSWORD = ''
    DB_HOST = 'localhost'
    DB_NAME = 'stock_apis'
    CSV_FILE_PATH = csv_filename
    TABLE_NAME = 'global_quote_endpoint'

    # Create a database engine using SQLAlchemy
    engine = create_engine(f'mysql+mysqlconnector://{DB_USER}:{DB_PASSWORD}@{DB_HOST}/{DB_NAME}')

    # Read the CSV file into a Pandas DataFrame
    df = pd.read_csv(CSV_FILE_PATH)

    # Insert the data into the MySQL table
    # if_exists='replace' drops previous table and creates new one with updated data
    df.to_sql(TABLE_NAME, con=engine, index=False, if_exists='replace')

    print(f"Data from {CSV_FILE_PATH} successfully imported into table {TABLE_NAME}.")

    # Close the connection (handled by the engine implicitly, but good practice to be aware)
    engine.dispose()

# No longer need an external file keeping track of run times, program now throws "KeyboardInterrupt" error
# if run again before previous run is complete

# "KeyboardInterrupt" error cancels the last run and immediately proceeds with the new run

# With the calls evenly spread out with time.sleep(), program will not be able to run again until all 
# tickers are processed

# Also spreading out the calls evenly will ensure the rate limit will never be hit

# Something to do in the future: Plot data