# https://www.youtube.com/watch?v=LosIGgon_KM


### IMPORT STATEMENTS ###
import csv
import os
import json
import requests
import re
import time
from urllib.parse import quote_plus as q
import matplotlib.pyplot as plt
import shutil

###  DIRECTORY WHERE ALL THE RESPONSE ARE STORED ###
CACHE_DIR = "url_cache"

### RATE LIMIT DURATION ###
RATE_LIMIT_DURATION = 1

### CSV FILE NAME CONTAINING COMPANY  NAME BY TICKER ###
COMPANY_CSV_FILENAME = "/Volumes/Macintosh HD (MAIN)/Towson/TU 2020 Spring/ECON 431/proj/second time/web-scrape-stocks-graphs/sp500-list.csv"

### ALL THE TICKERS ###
TICKERS = []

### COMPANY NAMES FOR TICKER ###
COMPANY_NAMES_BY_TICKER = {}

### THIS IS USED TO AVOID THE REQUESTS IF RESPONSE IS IN CACHE ALREADY ###
ENABLE_REQUESTS = True

### GRAPH DIRECTORY ###
PLOTS_DIR = "ticker_plots"

###  COMPANY BASE URL FOR TICKERS ###
COMPANY_BASE_URLS_BY_TICKER = {
    "EL": "/stocks/charts/EL/estee-lauder",
    "GL": "/stocks/charts/GL/globe-life",
    "HWM": "/stocks/charts/HWM/howmet-aerospace",
    "IPG": "/stocks/charts/IPG/interpublic-group-of",
    "J": "/stocks/charts/J/jacobs-engineering-group",
    "LB": "/stocks/charts/LB/l-brands",
    "LHX": "/stocks/charts/LHX/l3harris-technologies-inc",
    "LIN": "/stocks/charts/LIN/linde",
    "NLOK": "/stocks/charts/NLOK/nortonlifelock",
    "O": "/stocks/charts/O/realty-income",
    "OTIS": "/stocks/charts/OTIS/otis-worldwide",
    "PEAK": "/stocks/charts/PEAK/healthpeak-properties",
    "RTX": "/stocks/charts/RTX/raytheon-technologies",
    "SO": "/stocks/charts/SO/southern",
    "T": "/stocks/charts/T/at-t",
    "TFC": "/stocks/charts/TFC/truist-financial",
    "TT": "/stocks/charts/TT/trane-technologies",
    "UA": "/stocks/charts/UA/under-armour",
    "VIAC": "/stocks/charts/VIAC/viacomcbs",
}

"""
THIS FUNCTION READ TICKERS and COMPANY NAME from the csv file (sp500-list.csv), and store them in TICKERS and COMPANY_NAMES_BY_TICKER;
import csv, this package is used to read CSV files in python.

READ ABOUT LIST FROM: https://www.w3schools.com/python/python_lists.asp
READ ABOUT DICTIONATY FROM: https://www.w3schools.com/python/python_dictionaries.asp
READ ABOUT Python I/O  (Read and Write) FROM: https://www.w3schools.com/python/python_file_open.asp
"""
def load_tickers_from_csv():
    with open(COMPANY_CSV_FILENAME, "r") as company_csv_file:
        company_reader = csv.reader(company_csv_file)
        for ticker, company_name in company_reader:
            TICKERS.append(ticker)
            COMPANY_NAMES_BY_TICKER[ticker] = company_name


"""
THIS FUNCTION if the result is not cached, fetch the TICKER_INFO using the url and saved the response in the cache.

READ HOW TO MAKE REQUEST TO A WEB PAGE: https://www.w3schools.com/python/module_requests.asp
"""
def cached_requests(url):
    ###  CACHED FILE RELATIVE PATH ###
    cached_filename = os.path.join(CACHE_DIR, q(url))
    contents = ""
    ### IF THE RESULT IS PRESENT IN  CACHED DIRECTORY ###
    if os.path.exists(cached_filename):
        with open(cached_filename, "r") as read_file:
            contents = read_file.read()
    else:
        print(f"Requesting URL: {url}")
        if ENABLE_REQUESTS is False:
            raise RuntimeError("Declining request as ENABLE_REQUESTS is False")

        # Rate limit our requests
        if RATE_LIMIT_DURATION:
            print(f"Pausing for {RATE_LIMIT_DURATION} seconds as rate limiting")
            time.sleep(RATE_LIMIT_DURATION)

        # Make our request and verify it was a 200
        req = requests.get(url)
        req.raise_for_status()

        ### SAVED THE RESULT IN THE CACHE ###
        contents = req.text
        if not os.path.exists(CACHE_DIR):
            os.mkdir(CACHE_DIR)
        with open(cached_filename, "w") as write_file:
            write_file.write(contents)
    return contents


"""
FOR A TICKER, this function fetch the financial_statements and balance_sheet.

READ PYTHON JSON Parsing : https://www.w3schools.com/python/python_json.asp
READ regular expression search in python : https://www.w3schools.com/python/python_regex.asp
"""
def get_ticker_data(ticker):
    """
        -> for a ticker, fetch the base_url_path from dictionary (COMPANY_BASE_URLS_BY_TICKER);
        COMPANY_BASE_URLS_BY_TICKER["EL"] will return "/stocks/charts/EL/estee-lauder";
    """
    base_url_path = COMPANY_BASE_URLS_BY_TICKER.get(ticker, None)

    ### path is not present in the dictionary ###
    if base_url_path is None:
        """
            1. Try to fetch the base_url from the web browser using tricker "https://www.macrotrends.net/assets/php/all_pages_query.php?q=ABC" and load the result in ticker_info.
            2. if it is not possible to resovle base_url using ticker, fetch it using company_name.
            3. if it is still not possible to resolve the url, raise the error.
        """
        resolved_by = "ticker"
        ticker_info_str = cached_requests(f"https://www.macrotrends.net/assets/php/all_pages_query.php?q={q(ticker)}")
        ticker_info = json.loads(ticker_info_str)

        if ticker_info is None:
            company_name = COMPANY_NAMES_BY_TICKER[ticker]
            resolved_by = "company_name"
            ticker_info_str = cached_requests(
                f"https://www.macrotrends.net/assets/php/all_pages_query.php?q={q(company_name)}")
            ticker_info = json.loads(ticker_info_str)

        if ticker_info is None:
            company_name = COMPANY_NAMES_BY_TICKER[ticker]
            raise AssertionError(f"No ticker info found for {ticker} ({company_name}), requires hardcoding")

        """
            {"name": "AmerisourceBergen (ABC) - Revenue","url": "/stocks/charts/ABC/amerisourcebergen/revenue"},

            Validating the fetched base_url, it should start with /stocks/charts/ and it should contain 5 '/'
            if base_url is not valid, throw an error.
        """
        first_url_path = ticker_info[0]["url"]
        # Sanity check our URL
        if not first_url_path.startswith(f"/stocks/charts/{ticker}/") or first_url_path.count("/") != 5:
            print(ticker, COMPANY_NAMES_BY_TICKER[ticker], ticker_info)
            raise AssertionError(f"First URL in all pages query doesn't contain ticker. " +
                                 f"Expected: /stocks/charts/:ticker/:name/:phrase, actual: {first_url_path} (resolved_by {resolved_by})")

        base_url_path = os.path.dirname(first_url_path)

    ###  FETCH THE FINANCE STATEMENTS using the base_url_path ###
    financial_statements_url = "https://www.macrotrends.net/" + base_url_path + "/financial-statements"
    financial_statements_html = cached_requests(financial_statements_url)

    ###  FETCH THE BALANCE using the base_url_path ###
    balance_sheet_url = "https://www.macrotrends.net/" + base_url_path + "/balance-sheet"
    balance_sheet_html = cached_requests(balance_sheet_url)

    ### FIND THE financial_statements_data from the SOURCE HTML using regex search ###
    financial_statements_data_str = re.search(r"var originalData = ([^\n]+);", financial_statements_html)[1]
    financial_statements_data = json.loads(financial_statements_data_str)

    ### FIND THE balance_sheet from the SOURCE HTML using regex search ###
    balance_sheet_data_str = re.search(r"var originalData = ([^\n]+);", balance_sheet_html)[1]
    balance_sheet_data = json.loads(balance_sheet_data_str)

    for data in (financial_statements_data, balance_sheet_data):
        for field in data:
            field_key = re.search(r">([^<]+)<", field["field_name"])[1]
            del field["field_name"]
            del field["popup_icon"]

            for key, value in field.items():
                new_value = None
                if not isinstance(value, str):
                    raise AssertionError(
                        f"Expected all field values to be strings, received {key}: {value} ({value.__class__})")
                if value == "":
                    new_value = None
                elif "." in value:
                    new_value = float(value)
                else:
                    new_value = int(value, 10)
                field[key] = new_value

                # Save our key now that we're done with iteration
            field["key"] = field_key

    financial_statements_by_key = {}
    balance_sheet_by_key = {}
    """
        data: [{'2019-12-31': 4140.0,  '2018-12-31': 4086.0,  '2017-12-31': 9610.0, '2005-12-31': 2956.093, 'key': 'Cash On Hand'}]
        financial_statements_by_key -> {'Cash On Hand': {'2019-12-31': 4140.0,  '2018-12-31': 4086.0,  '2017-12-31': 9610.0, '2005-12-31': 2956.093}}
    """
    for data, data_by_key in (
            (financial_statements_data, financial_statements_by_key), (balance_sheet_data, balance_sheet_by_key)):
        for field in data:
            data_by_key[field["key"]] = field
            del field["key"]

    return {
        "financial_statements": financial_statements_by_key,
        "balance_sheet": balance_sheet_by_key,
    }


"""
THIS FUNCTION PERFORM DIVISION if a and b both are not None and B is not equal to 0. 
"""
def divide_or_none(a, b):
    if a is not None and b is not None and b != 0:
        return a / b
    return None


"""
THIS FUNCTION FETCH THE ticker_data from the url for the very first time.
"""
def load_data_in_cache():
    for ticker in TICKERS:
        try:
            print("TICKERT WE ARE CHECKING -> " + str(ticker))
            ticker_data = get_ticker_data(ticker)
            # print(f"Loaded data for {ticker}")
        except AssertionError as exc:
            print(f"AssertionError for {ticker}")
            print("    " + str(exc))
        except RuntimeError as exc:
            print(f"RuntimeError for {ticker}")
            print("    " + str(exc))


"""
THIS FUNCTION fetch the Debt/EBIT, ROA, Debt/Asset, EBITDA % from the ticker_data.

Sample use:
ticker_data{"balance_sheet" : {'Cash On Hand': {'2019-12-31': 4140.0}, 
                'Receivables': {'2019-12-31': 5425.0}, 
                'Inventory': {'2019-12-31': 4316.0},
                'Pre-Paid Expenses': {'2019-12-31': 1786.0}, 
                'Other Current Assets': {'2017-12-31': 20.0}, 
                'Total Current Assets': {'2019-12-31': 15667.0}, 
                'Property, Plant, And Equipment': {'2019-12-31': 8038.0}, 
                'Long-Term Investments': {'2019-12-31': 883.0}, 
                'Goodwill And Intangible Assets': {'2019-12-31': 40220.0,}, 
                'Other Long-Term Assets': {'2017-12-31': 176.0}, 
                'Total Long-Term Assets': {'2019-12-31': 52220.0}, 
                'Total Assets': {'2019-12-31': 67887.0}, 
                'Total Current Liabilities': {'2019-12-31': 10863.0}, 
                'Long Term Debt': {'2019-12-31': 16661.0}, 
                }}

    if we want to fetch debt_asset for a ticker, which is equal to ticker_data["balance_sheet"]["Long Term Debt"]/ticker_data["balance_sheet"][Total Assets"],
    use the calculation_for_graph with following paramters
    calculation_for_graph(ticker, ticker_data, dates, "balance_sheet", "balance_sheet", "Long Term Debt", "Total Assets", "Debt/Asset")
"""
def calculation_for_graph(ticker, ticker_data, dates, key1, key2, key3, key4, display_name):
    result = []
    for date in dates:
        val_1 = ticker_data[key1][key3][date]
        val_2 = ticker_data[key2][key4][date]
        value = divide_or_none(val_1, val_2)
        result.append(value)
        print(f"{display_name} for {ticker}, {date}: {value}")
    return result


### DELETE THE CURRENT DIRECTORY IF EXIST and CREATE IT AGAIN TO SAVE PLOTS ###
def create_plot_dir(ticker_directory):
    if os.path.exists(ticker_directory):
        print("CLEARING THE DIRECTORY")
        shutil.rmtree(ticker_directory)
    mode = 0o777
    os.makedirs(ticker_directory, mode)


def plot_chart(xData, yData, ticker_directory, legend, ticker):
    fig = plt.figure(figsize=(50, 30))
    plt.plot(xData, yData)
    plt.legend(labels=[legend], loc="best", borderaxespad=1.5, title='EBIDTA % Graph for ' + str(ticker), prop={'size': 20})

#    plt.show()
    fig.savefig(ticker_directory + "/" + str(legend) + '.png')
    plt.close()


"""
FOR A TICKER, this fetch all four dimensions (debt_ebit, roa, debt_asset, ebidta) and plot sub_graph for them using matplotlib.

FOR matplotlib, plots and subplots: https://www.tutorialspoint.com/matplotlib/index.htm, go through each topic.
"""
def calculate_and_plot_chart(ticker, ticker_data, dates):
    ticker_directory = PLOTS_DIR + "/" + ticker
    create_plot_dir(ticker_directory)
    ### for a Tickter FETCH THE debt_ebit from ticker_data ###
    debt_ebit = calculation_for_graph(ticker, ticker_data, dates, "balance_sheet", "financial_statements",
                                      "Long Term Debt", "EBIT", "Debt/EBIT")
    ### for a Tickter FETCH THE ROA from ticker_data ###
    roa = calculation_for_graph(ticker, ticker_data, dates, "financial_statements", "balance_sheet", "Net Income",
                                "Total Assets", "ROA")
    ### for a Tickter FETCH THE Debt/Asset from ticker_data ###
    debt_asset = calculation_for_graph(ticker, ticker_data, dates, "balance_sheet", "balance_sheet", "Long Term Debt",
                                       "Total Assets", "Debt/Asset")
    ### for a Tickter FETCH THE EBITDA % from ticker_data ###
    ebidta = calculation_for_graph(ticker, ticker_data, dates, "financial_statements", "financial_statements", "EBITDA",
                                   "Revenue", "EBITDA %")

    plot_chart(dates, debt_ebit, ticker_directory, "debt_ebit", ticker)
    plot_chart(dates, roa, ticker_directory, "roa", ticker)
    plot_chart(dates, debt_asset, ticker_directory, "debt_asset", ticker)
    plot_chart(dates, ebidta, ticker_directory, "ebidta_percentage", ticker)




### FOR EACH TICKER, fetch the data, and plot the graph ###
def create_charts():
    for ticker in TICKERS:
        print("TICKERT WE ARE CHECKING -> " + str(ticker))
        ticker_data = get_ticker_data(ticker)
        debt_all = ticker_data["balance_sheet"]["Long Term Debt"]
        dates = [date for date in debt_all.keys()]
        calculate_and_plot_chart(ticker, ticker_data, dates)


### MAIN FUNCTION ###
def main():
    load_tickers_from_csv()  # READ THE DATA FROM CSV FILE
    load_data_in_cache()  # LOAD THE DATA FROM THE CACHE
    create_charts()  # CREATE THE CHART


if __name__ == "__main__":
    main()