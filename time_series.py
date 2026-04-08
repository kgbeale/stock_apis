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
            url = f'https://www.alphavantage.co/query?function=TIME_SERIES_{returns}_ADJUSTED&symbol={tickers[i]}&outputsize=full&apikey={api_key}'
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
    size = 36 # how many days/months of data
    returns = "Monthly"
    api_key = "STNE15X0T16UDA4F"
    ret_stock = "FCNTX"
    ret_market = "VUG"
    tickers = [ret_stock, ret_market]

    # Add quarterly returns
    # Try using monthly return data to calculate quarterly returns instead of pulling from alpha vantage
    if returns == "Monthly":
        quarterly = True # only calculate quarterly data with monthly data,
                         # change to false to keep monthly data

    # Look at a mutual fund
    # Fidelity Select Tech Hardware (FDCPX)

    # Find out expense ratio
    # 0.69%

    # What is the benchmark they are trying to outperform?
    # S&P 500 (SPY)
    

    # Find an ETF that is passive (not trying to outperform benchmark)
    # First Trust International Equity Opportunities (FPXI)

    # Expense ratio
    # .70%

    # Benchmark
    # IPOX International Index (IPXI)

    # yahoo finance
    
    # ETFs are considered tax efficient because the fund doesn't have to buy and sell stocks

    calls_per_minute = 75
    interval = 60.0 / calls_per_minute  # Time between calls in seconds
    json_cache = f"time_series_{returns}_adjusted.json"
    csv_filename = f"time_series_{returns}_adjusted.csv"
    new_data = True # set to true to pull new data from alpha vantage
    data = fetch_data(update = new_data, json_cache = json_cache) # Function to use existing data or pull new data from alpha vantage

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
    df['Adjusted Close Price'] = pd.to_numeric(df['Adjusted Close Price'], errors='coerce')
    df['Return'] = df['Adjusted Close Price'].pct_change()
    df['Date'] = pd.to_datetime(df['Date'])

    # pivot dataframe based on date and export to csv
    wide_df_full = df.pivot(index='Date', columns='Ticker', values='Return')
    wide_df_adjusted = wide_df_full.tail(size)
    for i in range(len(wide_df_adjusted.columns)):
        wide_df_adjusted = wide_df_adjusted.dropna(subset=wide_df_adjusted.columns[i]) # Drop rows that have 'NaN' values
    wide_df_adjusted['Diff'] = wide_df_adjusted[ret_market] - wide_df_adjusted[ret_stock] # Difference between stock and market
    # cumulative returns for stock and market
    wide_df_adjusted[f'cumret_{ret_market}'] = (1+wide_df_adjusted[ret_market]).cumprod()-1
    wide_df_adjusted[f'cumret_{ret_stock}'] = (1+wide_df_adjusted[ret_stock]).cumprod()-1
    if quarterly == True:
        # convert monthly to quarterly
        wide_df_adjusted = wide_df_adjusted.resample('Q').mean()
        wide_df_adjusted.to_csv("time_series_quarterly.csv")
    else:
        wide_df_adjusted.to_csv(csv_filename)

    # Plot dataframe
    sns.regplot(x=wide_df_adjusted[ret_market], y=wide_df_adjusted[ret_stock])
    plt.title('Beta Visualization: Stock vs Market')
    plt.xlabel(f'Market Returns: {ret_market}')
    plt.ylabel(f'Stock Returns: {ret_stock}')
    plt.show()
    print(wide_df_adjusted)
    
    # Calculate beta
    lin_reg = linregress(wide_df_adjusted[ret_market], wide_df_adjusted[ret_stock]) # calculate slope and intercept
    # beta = lin_reg.slope # slope represents the beta of the stock
    print(lin_reg)
    # print('Beta: ', beta)

    # 3 ways to calculate beta
    # Beta measures volatility of stock
    # Beta = Slope of the regression line
    # Beta = Covariance(ret_y, ret_mkt) / Variance(ret_mkt)
    # Beta = Correlation * std_dev(y_ret) / std_dev(x_ret)
    # R^2 = Correlation^2

    # Calculate standard deviation of stock
    std_dev_y_ret = statistics.stdev(wide_df_adjusted[ret_stock])

    # Calculate standard deviation of market
    std_dev_x_ret = statistics.stdev(wide_df_adjusted[ret_market])

    # Calculate correlation (r value, pulled from linear regression)
    correlation = lin_reg.rvalue

    # Calculate Beta using above values
    beta = correlation * (std_dev_y_ret / std_dev_x_ret)
    print('Beta: ', beta)

    # Show intercept in print statement
    intercept = lin_reg.intercept
    print('Intercept: ', intercept)

    # Calculate average return for both market and stock

    # Average return for stock
    avg_ret_y = wide_df_adjusted[ret_stock].mean()
    print(f'Average Return {ret_stock}: ', avg_ret_y)

    # Average return for market
    avg_ret_x = wide_df_adjusted[ret_market].mean()
    print(f'Average Return {ret_market}: ', avg_ret_x)

    # Plug average return for market into CAPM to calculate expected return for stock
    # Calculating daily return RFR (assuming RFR is 4%): Daily Return RFR = 1.04^(1/365)-1
    daily_rfr = 1.04**(1/365)-1
    E_r_voog = daily_rfr + beta * (avg_ret_x - daily_rfr) # CAPM formula: E(r) = RFR + Beta(e(r_mkt) - RFR))
    print(f'Expected Return {ret_stock}: ', E_r_voog)

    # Calculate R-Squared
    y_pred = (beta * wide_df_adjusted[ret_market]) + lin_reg.intercept # calculate predicted values for y
    r2 = r2_score(wide_df_adjusted[ret_stock], y_pred)
    print('R-Squared: ', r2) # Percentage of volatility explained by the market

    # # Create another pandas dataframe with just 2 columns (symbol, quantity), default value 1000 for both
    # symbol_quantity = []
    # symbol_quantity_csv = "daily_adjusted_symbol_quantity.csv"
    # symbol_quantity_dict = {'symbol': '1000', 'quantity': '1000'}
    # symbol_quantity.append(symbol_quantity_dict)
    # df = pd.DataFrame(symbol_quantity)
    # df.to_csv(symbol_quantity_csv)

    # log data to mysql database
    # MySQL database connection details
    DB_USER = 'root'
    DB_PASSWORD = ''
    DB_HOST = 'localhost'
    DB_NAME = 'stock_market_analysis'
    if quarterly == True:
        CSV_FILE_PATH = "time_series_quarterly.csv"
        TABLE_NAME = 'time_series_quarterly_adjusted'
    else:
        CSV_FILE_PATH = csv_filename
        if returns == "Monthly":
            TABLE_NAME = 'time_series_monthly_adjusted'
        elif returns == "Daily":
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

    # Clean code to make it reusable
    # Read from csv or pull data from alpha vantage
    # See if I can produce dataframe that represents monthly returns
    # Investments should be compared with comparable investments (benchmark)

    # Try to switch to monthly returns in this file
    # Map out before coding
    # Code does not have to be complete this week

    # ETF (Exchange traded fund) has 3 letters in ticker, mutual fund usually has 4-5 letters in ticker
    # Mutual fund is an almost always active fund, trying to outperform their benchmark
    # ETF can be bought and sold as a stock
    # A lot of ETFs are passive and not necessarily trying to outperform their benchmark

    # Update code to parse number of trading days historically (entire data history instead of just past 100 days)
    # Input parameter for certain number of days (ex: out of probably 20000 days, only look at 252 days (past year in trading days))