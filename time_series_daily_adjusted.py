import time
import requests
import pandas as pd
import json
from datetime import datetime
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
            url = f'https://www.alphavantage.co/query?function=TIME_SERIES_DAILY_ADJUSTED&symbol={tickers[i]}&apikey={api_key}'
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
    tickers = ["UBS", "IBM"]
    calls_per_minute = 75
    interval = 60.0 / calls_per_minute  # Time between calls in seconds
    json_cache = "time_series_daily_adjusted.json"
    csv_filename = "time_series_daily_adjusted.csv"
    data = fetch_data(update = True, json_cache = json_cache) # Call function to fetch existing data or make new api call
    # Set update to true for new data

    # Create lists for each column to be added to dataframe
    index = 0 # set initial index to 0
    index_list = [] # index list
    ticker_list = [] # ticker list
    date_list = [] # date list
    adjusted_close_list = [] # adjusted close list

    # Loop through data and append to lists
    for i in range(len(data)):
        for key, value in data[i].items():
            for key1, value1 in value.items():
                try:
                    format = '%Y-%m-%d'
                    datetime.strptime(key1, format)
                    index += 1
                    index_list.append(index)
                    ticker_list.append(tickers[i])
                    date_list.append(key1)
                    adjusted_close_list.append(value1['5. adjusted close'])
                except ValueError:
                    continue
    
    # create dictionary of each list and then convert to dataframe
    time_series_dict = {"Index": index_list, "Ticker": ticker_list, "Date": date_list,
                   "Adjusted Close Price" : adjusted_close_list}
    df = pd.DataFrame(time_series_dict)
    df.to_csv(csv_filename)

    # Date column for dates in dataframe
    # df = (pd.DataFrame.from_dict(time_series=, orient="index")
    #.rename_axis("date")
    #.reset_index())

    # df["date"] = pd.to_datetime(df["date"])
    # df["close_price"] = df["5. adjusted close"].astype(float)
    # df = df.sort_values("date").reset_index(drop=True)

    # Create another pandas dataframe with just 2 columns (symbol, quantity), default value 1000 for both
    symbol_quantity = []
    symbol_quantity_csv = "time_series_symbol_quantity.csv"
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
    TABLE_NAME = 'time_series_daily_adjusted'

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

    # Took screenshot of ideal dataframe format
    # Try multiple tickers