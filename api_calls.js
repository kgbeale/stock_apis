'use strict';
let request = require('request');

let api_key = "STNE15X0T16UDA4F";
let array = ["SPY","QQQ","IAU", "VONE", "VONG", "VONV", "IWM", "IEF"];
let url = `https://www.alphavantage.co/query?function=GLOBAL_QUOTE&symbol=IBM&apikey={api_key}`;

// Function to delay execution
const delay = (ms) => new Promise(resolve => setTimeout(resolve, ms));

// Sequential execution with delays
let promies = array.map(async(Element, index) => {
  // Wait for (index * 800ms) before making the call
  // This spaces out calls by 0.8 seconds
  await delay(index * 800);

  return quotes_global.trigger({additionalScope: {symbol:
    ele}});
});

console.log(promises);
return Promise.all(promises);