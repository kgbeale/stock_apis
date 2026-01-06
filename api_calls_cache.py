import time
import requests
import pandas as pd
import json

api_key = "STNE15X0T16UDA4F"
tickers = ["IBM", "MSFT", "AAPL", "UBS"]
calls_per_minute = 75
interval = 60.0 / calls_per_minute  # Time between calls in seconds
json_filename = "global_quote_endpoint.json"
csv_filename = "global_quote_endpoint.csv"

all_data = []
for i in range(len(tickers)):
    url = f'https://www.alphavantage.co/query?function=GLOBAL_QUOTE&symbol={tickers[i]}&apikey={api_key}'
    r = requests.get(url)
    data = r.json()
    all_data.append(data)
        
    # Calculate sleep time to maintain rate limit
    start = time.time()
    elapsed = time.time() - start
    sleep_time = max(0, interval - elapsed)
    time.sleep(sleep_time)

# Convert json to csv without reading external file
df = pd.json_normalize(all_data) # converts semi-structured json data into flat table (dataframe)
df.to_csv(csv_filename)
    
# write to json file
with open(json_filename, "w") as f:
    json.dump(all_data, f, indent=4)

# No longer need an external file keeping track of run times, program now throws "KeyboardInterrupt" error
# if run again before previous run is complete

# "KeyboardInterrupt" error cancels the last run and immediately proceeds with the new run

# With the calls evenly spread out with time.sleep(), program will not be able to run again until all 
# tickers are processed

# Also spreading out the calls evenly will ensure the rate limit will never be hit

# Json caching