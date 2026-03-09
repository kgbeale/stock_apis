import time
import requests
import pandas as pd
import json
from datetime import datetime
import seaborn as sns
import matplotlib.pyplot as plt
from scipy.stats import linregress
from sklearn.metrics import r2_score
import statistics
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
    
    # pull new data from alpha vantage
    if not json_data:
        json_data = []
        for i in range(len(tickers)):
            url = f'https://www.alphavantage.co/query?function=TIME_SERIES_MONTHLY_ADJUSTED&symbol={tickers[i]}&apikey={api_key}'
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
    tickers = ["SPY", "VOOG"] # tickers[0] = market, tickers[1] = stock
    calls_per_minute = 75
    interval = 60.0 / calls_per_minute  # Time between calls in seconds
    json_cache = "time_series_monthly_adjusted.json"
    csv_filename = "time_series_monthly_adjusted.csv"
    data = fetch_data(update = True, json_cache = json_cache) # Function to use existing data or pull new data from alpha vantage
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
                # Remove numbers from value names (ex. '5. adjusted close' becomes 'adjusted close')
                if isinstance(value1, dict):
                    new_value = {}
                    for key2, value2 in value1.items():
                        parts = key2.split('. ')
                        for part in parts:
                            new_value[part] = value2
                    keys_to_remove = []
                    for key3, value3 in new_value.items():
                        try:
                            int(key3)
                            keys_to_remove.append(key3)
                        except ValueError:
                            continue
                    for j in keys_to_remove:
                        del new_value[j]
                    try:
                        format = '%Y-%m-%d'
                        datetime.strptime(key1, format)
                        index += 1
                        index_list.append(index)
                        ticker_list.append(tickers[i])
                        date_list.append(key1)
                        adjusted_close_list.append(new_value['adjusted close'])
                    except ValueError:
                        continue
                else:
                    continue
    
    # create dictionary of each list and then convert to dataframe
    time_series_dict = {"Index": index_list, "Ticker": ticker_list, "Date": date_list,
                   "Adjusted Close Price" : adjusted_close_list}
    df = pd.DataFrame(time_series_dict)
    df['Adjusted Close Price'] = pd.to_numeric(df['Adjusted Close Price'], errors='coerce')
    df['Return'] = df['Adjusted Close Price'].pct_change()
    df['Date'] = pd.to_datetime(df['Date'])

    # pivot dataframe based on date and export to csv
    wide_df = df.pivot(index='Date', columns='Ticker', values='Return')
    for i in range(len(wide_df.columns)):
        wide_df = wide_df.dropna(subset=wide_df.columns[i]) # Drop rows that have 'NaN' values
    wide_df['Diff'] = wide_df[tickers[0]] - wide_df[tickers[1]] # Difference between stock and market
    # cumulative returns for stock and market
    wide_df[f'cumret_{tickers[0]}'] = (1+wide_df[tickers[0]]).cumprod()-1
    wide_df[f'cumret_{tickers[1]}'] = (1+wide_df[tickers[1]]).cumprod()-1
    wide_df.to_csv(csv_filename)

    # Plot dataframe
    sns.regplot(x=wide_df[tickers[0]], y=wide_df[tickers[1]])
    plt.title('Beta Visualization: Stock vs Market')
    plt.xlabel(f'Market Returns: {tickers[0]}')
    plt.ylabel(f'Stock Returns: {tickers[1]}')
    plt.show()
    print(wide_df)
    
    # Calculate beta
    lin_reg = linregress(wide_df[tickers[0]], wide_df[tickers[1]]) # calculate slope and intercept
    # beta = lin_reg.slope # slope represents the beta of the stock
    print(lin_reg)
    # print('Beta: ', beta)

    # 3 ways to calculate beta
    # Beta = Slope of the regression line
    # Beta = Covariance(ret_y, ret_mkt) / Variance(ret_mkt)
    # Beta = Correlation * std_dev(y_ret) / std_dev(x_ret)
    # R^2 = Correlation^2

    # Calculate standard deviation of stock
    std_dev_y_ret = statistics.stdev(wide_df[tickers[1]])

    # Calculate standard deviation of market
    std_dev_x_ret = statistics.stdev(wide_df[tickers[0]])

    # Calculate correlation (r value, pulled from linear regression)
    correlation = lin_reg.rvalue

    # Caculate Beta using above values
    beta = correlation * (std_dev_y_ret / std_dev_x_ret)
    print('Beta: ', beta)

    # Calculate average return for both market and stock

    # Average return for stock
    avg_ret_y = wide_df[tickers[1]].mean()
    print(f'Average Return {tickers[1]}: ', avg_ret_y)

    # Average return for market
    avg_ret_x = wide_df[tickers[0]].mean()
    print(f'Average Return {tickers[0]}: ', avg_ret_x)

    # Plug average return for market into CAPM to calculate expected return for stock
    # Calculating daily return RFR (assuming RFR is 4%): Daily Return RFR = 1.04^(1/365)-1
    daily_rfr = 1.04**(1/365)-1
    E_r_voog = daily_rfr + beta * (avg_ret_x - daily_rfr) # CAPM formula: E(r) = RFR + Beta(e(r_mkt) - RFR))
    print(f'Expected Return {tickers[1]}: ', E_r_voog)

    # Calculate R-Squared
    y_pred = (beta * wide_df[tickers[0]]) + lin_reg.intercept # calculate predicted values for y
    r2 = r2_score(wide_df[tickers[1]], y_pred)
    print('R-Squared: ', r2) # Percentage of volatility explained by the market

    # Create another pandas dataframe with just 2 columns (symbol, quantity), default value 1000 for both
    symbol_quantity = []
    symbol_quantity_csv = "monthly_adjusted_symbol_quantity.csv"
    symbol_quantity_dict = {'symbol': '1000', 'quantity': '1000'}
    symbol_quantity.append(symbol_quantity_dict)
    df = pd.DataFrame(symbol_quantity)
    df.to_csv(symbol_quantity_csv)

    # log data to mysql database
    # MySQL database connection details
    DB_USER = 'root'
    DB_PASSWORD = ''
    DB_HOST = 'localhost'
    DB_NAME = 'stock_market_analysis'
    CSV_FILE_PATH = csv_filename
    TABLE_NAME = 'time_series_monthly_adjusted'

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

    # Clean code to make it reusable
    # Read from csv or pull data from alpha vantage
    # See if I can produce dataframe that represents monthly returns
    # Investments should be compared with comparable investments (benchmark)