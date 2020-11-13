import datetime
import sys, os
import quandl

def download_data(quandl_code, from_date):
    print("Downloading: [{}]".format(quandl_code))
    df = quandl.get(quandl_code, start_date=from_date)
    print("Shape of the downloaded data: ", df.shape)
    print("The first 5 rows of the data: \n", df.head())
    print("The last 5 rows of the data: \n", df.tail())
    df.to_csv(os.path.join("..", "data", "MarketData", "Quandl", quandl_code.replace("/", "_")+".csv"))

if __name__ == '__main__':
    pg_name = sys.argv[0]
    args = sys.argv[1:]
    fred_all = ('DFEDTAR', 'DFEDTARL', 'DFEDTARU', 'DFF', 'GDPC1', 'GDPPOT', 'PCEPILFE', 'CPIAUCSL', 'UNRATE', 'PAYEMS', 'RRSFS', 'HSN1F')
    ism_all = ('MAN_PMI', 'NONMAN_NMI')
    treasury_code = 'USTREASURY/YIELD'

    if (len(args) != 2) and (len(args) != 3):
        print("Usage: python {} api_key from_date [Quandl Code]".format(pg_name))
        print("   api_key: Copy from your Quandl Account")
        print("   from_date: Specify the start date in yyyy-mm-dd format")
        print("   Quandl Code: Optional to Specify Target. (e.g. FRED/DFEDTAR) If not specified, all data are downloaded.")
        print("\n You specified: ", ','.join(args))
        sys.exit(1)

    if len(args) == 2:
        all_data = True
    else:
        all_data = False
        quandl_code = args[2]

    quandl.ApiConfig.api_key = args[0]
    from_date = args[1]
    try:
        datetime.datetime.strptime(from_date, '%Y-%m-%d')
    except ValueError:
        print("from_date should be in yyyy-mm-dd format. You gave: ", from_date)
        sys.exit(1)

    if all_data:
        for dataset_code in fred_all:
            download_data("FRED/" + dataset_code, from_date)
        for dataset_code in ism_all:
            download_data("ISM/" + dataset_code, from_date)
        download_data(treasury_code, from_date)
    else:
        download_data(quandl_code, from_date)
