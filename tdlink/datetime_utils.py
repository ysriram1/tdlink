from datetime import datetime
from dateutil import parser
from pytz import timezone, utc

CHICAGO_TZ = timezone('America/Chicago')

# converts to Unix epoch time
# essentially time since 01/01/1970
# default timezone is GMT (not CST or CDT)
# date format: mm/dd/yyyy
# time format: hh:mm:ss
# if milliseconds is false (returns in seconds)
def convert_to_epoch_time(date, time=None, milliseconds=True):
    if time:
        date_time_str = date + ' ' + time
    else:
        date_time_str = date + ' ' + '14:30:00'
    date_time_obj = datetime.strptime(date_time_str, '%m/%d/%Y %H:%M:%S')
    epoch = datetime.utcfromtimestamp(0)
    in_seconds = (date_time_obj - epoch).total_seconds()
    if milliseconds: return int(in_seconds * 1000)
    else: return int(in_seconds)

# converts unix epoch time to datetime object
# also makes the dt object tz aware first and the converts to GMT
def convert_from_epoch_time(epoch_time, return_string=False, milliseconds=True):
    if milliseconds: epoch_time = epoch_time//1000
    date_time_obj = datetime.fromtimestamp(epoch_time)
    # convert local timezone to gmt
    date_time_obj = CHICAGO_TZ.localize(date_time_obj) # set local tz
    date_time_obj = date_time_obj.astimezone(utc) # convert
    date_time_obj = date_time_obj.replace(tzinfo=None) # drop tz part
    if return_string: return date_time_obj.isoformat()
    else: return date_time_obj

# returns date in ISO 8601 format
# date and time should be in GMT (not CST or CDT)
# date format: mm/dd/yyyy
# time format: hh:mm:ss
def iso_date_time(date, time=None):
    if time:
        date_time_str = date + ' ' + time
    else:
        date_time_str = date + ' ' + '14:30:00'
    date_time_obj = datetime.strptime(date_time_str, '%m/%d/%Y %H:%M:%S')
    return date_time_obj.isoformat()

# returns a date time obj byt processing a ISO 8601 string
def return_dt_from_iso(iso_str):
    dt_obj = parser.parse(iso_str)
    # remove timezone and convert to gmt
    dt_obj = dt_obj - dt_obj.tzinfo.utcoffset('second')
    dt_obj = dt_obj.replace(tzinfo=None)
    return dt_obj

# converts unix epoch time to datetime object
# given a expiry date, strike, kind (Call, Put), converts to an option symbol
# dateformat: mm/dd/YYYY
# the underlying equity symbol
def convert_to_optsym(symbol, date, strike, kind):
    # check if expiry is a Friday
    date_time_obj = datetime.strptime(date, '%m/%d/%Y')
    if date_time_obj.weekday() != 4:
        print('Warning, expiry date is not a Friday!')
    if kind.lower() == 'call': kind = 'C'
    if kind.lower() == 'put': kind = 'P'
    date_parts = date.split('/')
    date_clean = date_parts[0]+date_parts[1]+date_parts[2][-2:]
    strike = str(strike); symbol = symbol.upper()
    option_symbol = symbol + '_' + date_clean + kind + str(strike)
    return option_symbol


# converts the date and time values into a single datetime object
# NOTE: for trading economics calendar only!
def to_date_time(date, time):
    date = ' '.join(date.split(' ')[1:]) # remove the verbal day
    if len(time.strip()) == 0: return datetime.strptime(date, '%B %d %Y')
    else: return datetime.strptime(date+' '+time, '%B %d %Y %I:%M %p')
