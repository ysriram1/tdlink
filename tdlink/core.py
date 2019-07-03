'''
connect to tdameritrade api and get data
get live and historical stock and live option data from TDAmeritrade

NOTE: You need to first get a code from TDAmeritrade by logging in. Follow these steps:
1) Go to TDAmeritrade developer: https://developer.tdameritrade.com/
2) Login and go to "My Apps"
3) Create an app. Use http://localhost as the callback url.
4) Go to this url: https://auth.tdameritrade.com/auth?response_type=code&redirect_uri=http://localhost&client_id=[YourAppName]@AMER.OAUTHAP
5) Enter your TD credentials and give premission
6) Once you login, you will be redirected to a url of this form https://localhost/?code=<code>
7) Copy the <code> part. Add it as a parameter to the TDAmeritrade class
8) The TDAmeritrade class should now work!

NOTE: The code you obtain is only valid for a limited period of time. If expired, follow steps again to get a new code.

'''

import requests
import json
from datetime import datetime
from .datetime_utils \
        import iso_date_time, convert_to_epoch_time, convert_from_epoch_time, return_dt_from_iso
import pandas as pd
import time
import urllib
# #HOME_DIR = '/Users/sriram/Desktop/ML/stock_market/auto_trader/'
# CREDENTIALS_FILE = 'tdameritrade_credentials.json'
#
# with open(CREDENTIALS_FILE, "r") as f:
#     credentials = json.load(f)

class TDlink:
    ''' This is the class for TDAmeritrade API '''

    def __init__(self,
                app_key, # required
                redirect_uri, # typically http://localhost
                code=None, # either refresh_token or code required
                refresh_token=None, # either refresh_token or code required
                return_raw_response=False, # if True none of the methods will process the responses
                ):
        '''
        Constructor for the TDAmeritrade class

        Attributes:
            app_key (str): the name of app created on tdameritrade developer site (aka api_key)
            redirect_uri (str): the url to which the output should be broadcasted (typically http://locahost)
            refresh_token (str): refresh token (optional)
            code (str): the uri decoded code (optional)
            return_raw_response (bool): if set to True, the http response is returned rather than the pandas df

        Note: Either the code or refresh token need to be provided
        '''
        if not code and not refresh_token:
            print('Either code or refresh token is needed. Follow instructions to obtain code.')
            raise
        self.request_url_template = 'https://api.tdameritrade.com/v1/'
        self.app_key = app_key # aka apikey
        self.client_id = app_key + '@AMER.OAUTHAP'
        if code: self.code = urllib.parse.unquote(code) # need to decode code first
        self.redirect_uri = redirect_uri
        if refresh_token:
            self.refresh_token = refresh_token
            self.refresh_access() # gets an access token using refresh token
        elif not refresh_token and self.code:
            self.get_tokens() # get refresh and access tokens using code
        else:
            print('Either a valid refresh token or valid code need to be provided')
            return
        # else:
        #     self.refresh_token = refresh_token
        #     self.access_token = access_token
        self.authorization = { # passed as a header to requests
                'Authorization': 'Bearer ' + self.access_token,
                }
        self.raw_response = return_raw_response

    # get the bearer access token and refresh token using code
    def get_tokens(self):
        ''' obtains the refresh token and the bearer access token using the code '''

        request_url = self.request_url_template + 'oauth2/token'
        data = {
            'grant_type':'authorization_code',
            'refresh_token':None,
            'access_type':'offline',
            'code':self.code,
            'client_id':self.client_id,
            'redirect_uri':self.redirect_uri
            }
        response = requests.post(request_url, data=data)
        try:
            self.access_token = response.json()['access_token']
            self.refresh_token = response.json()['refresh_token']
        except:
            print('please check the code you have provided')
            raise
        self.grant_time = time.time()


    # access token refresh using refresh token (new refresh token as generated and stored)
    def refresh_access(self):
        ''' uses refresh token to get bearer access token '''
        request_url = self.request_url_template + 'oauth2/token'
        data = {
            'grant_type':'refresh_token',
            'refresh_token':self.refresh_token,
            'access_type':'offline',
            'code':None,
            'client_id':self.client_id,
            'redirect_uri':self.redirect_uri
            }
        response = requests.post(request_url, data=data)
        self.access_token = response.json()['access_token']
        self.refresh_token = response.json()['refresh_token']
        self.grant_time = time.time()

    # https://developer.tdameritrade.com/price-history/apis/get/marketdata/%7Bsymbol%7D/pricehistory
    # returns the historical prices of an equity (doesnt work with options)
    # set period to False if using the date options
    def get_historical_prices(self,
                            symbol='QQQ',
                            period_type='day', # 'day'
                            period=2, # day: 1, 2, 3, 4, 5, 10* month: 1*, 2, 3, 6 year: 1*, 2, 3, 5, 10, 15, 20 ytd: 1*
                            frequency_type='minute', # day: minute* month: daily, weekly* year: daily, weekly, monthly* ytd: daily, weekly*
                            frequency=5, # minute: 1*, 5, 10, 15, 30 daily: 1* weekly: 1* monthly: 1*
                            start_date='06/01/2018', # mm/dd/yyyy
                            start_time=None, # hh:mm:ss
                            end_date='12/31/2018',
                            end_time=None,
                            extended_hours=True,
                            return_df=True # if False, returns a dictionary instead
                            ):
        '''
        Uses Price History API to get historical prices of a symbol.
        https://developer.tdameritrade.com/price-history/apis/get/marketdata/%7Bsymbol%7D/pricehistory
        Access link to get a explanation of parameters
        '''
        if abs(self.grant_time - time.time()) >= 1800: self.refresh_access() # access token needs to be refreshed every 1800 seconds
        request_url = self.request_url_template + 'marketdata/{}/pricehistory'.format(symbol)
        query_dict = {
            'apikey':self.app_key,
            'periodType':str(period_type),
            'period': str(period) if period else None,
            'frequencyType': frequency_type,
            'frequency':str(frequency),
            'startDate':None if period else str(convert_to_epoch_time(start_date, start_time)),
            'endDate':None if period else str(convert_to_epoch_time(end_date, end_time)),
            'needExtendedHoursData':'true' if extended_hours else 'false'
            }
        # add query params to url
        query_params = '?'
        for key, val in query_dict.items():
            if val: # skip the None values
                query_params += key + '=' + str(val) + '&'
        request_url = request_url + query_params[:-1] # remove last '&'
        response = requests.get(request_url, headers=self.authorization)
        if self.raw_response: return response

        # add to a dict and dataframe for east manipulation
        candles = response.json()['candles']
        df_cols = ['datetime', 'symbol', 'close', 'open', 'high', 'low', 'volume']
        df_dict = {key:[] for key in df_cols}
        for candle in candles:
            df_dict['symbol'].append(symbol)
            for key in df_dict.keys():
                if key == 'symbol': continue
                if key == 'datetime':
                    df_dict[key].append(convert_from_epoch_time(candle[key]))
                    continue
                df_dict[key].append(candle[key])
        if not return_df:
            return df_dict
        else:
            df = pd.DataFrame(df_dict)
            df = df.set_index('datetime')
            return df

    # https://developer.tdameritrade.com/quotes/apis
    # returns current quote (for ETF, Option, Stock etc)
    def get_current_quote(self,
                        symbol='QQQ',
                        to_return=['askPrice', 'bidPrice', 'totalVolume'] # refer to json in webpage
                        ):
        '''
        Retrieves the current price of a single symbol (this can also be an option)
        https://developer.tdameritrade.com/quotes/apis/get/marketdata/%7Bsymbol%7D/quotes
        Access link to get a explanation of parameters
        '''
        if abs(self.grant_time - time.time()) >= 1800: self.refresh_access() # access token needs to be refreshed every 1800 seconds
        request_url = self.request_url_template + 'marketdata/{}/quotes?apikey={}'.format(symbol,self.app_key)
        response = requests.get(request_url, headers=self.authorization)
        if self.raw_response: return response

        # process response
        response_dict = response.json()
        return_vals = [response_dict[symbol][key] for key in to_return]
        return return_vals

    # https://developer.tdameritrade.com/option-chains/apis/get/marketdata/chains
    # returns a table with the option symbol, date, and strike
    def get_options_chain(self,
                        symbol='QQQ', # symbol of underlying security
                        strike=None, # mention a specific strike
                        from_date='01/01/2020', # only expirations after this date (mm/dd/yyyy)
                        from_time=None,
                        to_date='01/30/2020', # only expirations before this date
                        to_time=None,
                        expiry_month='ALL', # option expiry month ALL or JAN
                        kind='OTM', # ITM, NTM, OTM, SAK (Strikes Above Market), ALL etc.
                        include_quotes=False, # if FALSE only returns the option names (use get_current_quote() to get value)
                        contract_type='CALL', # CALL, PUT
                        strikes=5, # number of strikes above or below at-the-money price
                        strategy='SINGLE',
                        return_df=True # if False, returns a dictionary instead
                        ):
        '''
        Returns a table with the option symbol, date, strike. use td.get_current_quote() to get current price of option.
        https://developer.tdameritrade.com/option-chains/apis/get/marketdata/chains
        Access link to get a explanation of parameters
        '''
        if abs(self.grant_time - time.time()) >= 1800: self.refresh_access() # access token needs to be refreshed every 1800 seconds
        request_url = self.request_url_template + 'marketdata/chains'
        query_dict = {
            'apikey':self.app_key,
            'symbol':symbol,
            'contractType':contract_type,
            'strikeCount':str(strikes),
            'includeQuotes':'FALSE' if not include_quotes else 'TRUE',
            'strategy':strategy,
            'range':kind,
            'fromDate':iso_date_time(from_date, from_time),
            'toDate':iso_date_time(to_date, to_time),
            'expMonth':expiry_month,
            'optionType':'S' # S - Standard, NS - Non-Standard, ALL
        }
        # add query params to url
        query_params = '?'
        for key, val in query_dict.items():
            if val: # skip the None values
                query_params += key + '=' + str(val) + '&'
        request_url = request_url + query_params[:-1] # remove last '&'
        response = requests.get(request_url, headers=self.authorization)
        if self.raw_response: return response

        # add response values to pd dataframe or dict
        dict_key = 'callExpDateMap' if contract_type == 'CALL' else 'putExpDateMap'
        response_dict = response.json()[dict_key]
        exp_date_strs = list(response_dict.keys())
        exp_date_time = [datetime.strptime(dt.split(':')[0], '%Y-%m-%d') for dt in exp_date_strs]
        df_cols = ['expiry', 'symbol', 'strike', 'option_type', 'description']
        df_dict = {key:[] for key in df_cols}
        for i,date_str in enumerate(exp_date_strs):
            dict_exp = response_dict[date_str]
            for strike_val in dict_exp.keys():
                df_dict['expiry'].append(exp_date_time[i])
                df_dict['option_type'].append(contract_type)
                df_dict['strike'].append(strike_val)
                df_dict['symbol'].append(dict_exp[strike_val][0]['symbol'])
                df_dict['description'].append(dict_exp[strike_val][0]['description'])
        if not return_df: return df_dict
        else: return pd.DataFrame(df_dict)

    # https://developer.tdameritrade.com/movers/apis/get/marketdata/%7Bindex%7D/movers
    # returns the top movers for a given index
    def get_movers_for_index(self,
                             symbol = 'DJI', # has to be an index DJI, SPX.X  etc
                             direction = None, # 'up' or 'down'. if None, returns both
                             change = None # 'value' or 'percent'. if None, defaults to percentage
                            ):
        '''
        returns the top movers for a given index (DJI).
        https://developer.tdameritrade.com/movers/apis/get/marketdata/%7Bindex%7D/movers
        Access link to get a explanation of parameters
        '''
        if abs(self.grant_time - time.time()) >= 1800: self.refresh_access() # access token needs to be refreshed every 1800 seconds
        symbol = symbol if symbol[0] == '$' else '$'+symbol
        request_url = self.request_url_template + 'marketdata/{}/movers'.format(symbol)
        query_dict = {
            'apikey': self.app_key,
            'direction': direction,
            'change': change
        }

        # add query params to url
        query_params = '?'
        for key, val in query_dict.items():
            if val: # skip the None values
                query_params += key + '=' + str(val) + '&'
        request_url = request_url + query_params[:-1] # remove last '&'
        response = requests.get(request_url, headers=self.authorization)
        if self.raw_response: return response

        # add response values to pd dataframe or dict
        response_json = response.json()
        return pd.DataFrame(response_json)
