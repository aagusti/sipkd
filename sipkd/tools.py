import os
import re
import mimetypes
import csv
from datetime import datetime
from types import (
    IntType,
    LongType,
    ListType,
    StringType,
    UnicodeType,
    BooleanType,
    )
import calendar    
from datetime import (
    date,
    datetime,
    timedelta,
    )
from random import choice
from string import (
    ascii_uppercase,
    ascii_lowercase,
    digits,
    )
import locale
import pytz
import io
from pyramid.threadlocal import get_current_registry


################
# Phone number #
################
MSISDN_ALLOW_CHARS = map(lambda x: str(x), range(10)) + ['+']

def get_msisdn(msisdn, country='+62'):
    for ch in msisdn:
        if ch not in MSISDN_ALLOW_CHARS:
            return
    try:
        i = int(msisdn)
    except ValueError, err:
        return
    if not i:
        return
    if len(str(i)) < 7:
        return
    if re.compile(r'^\+').search(msisdn):
        return msisdn
    if re.compile(r'^0').search(msisdn):
        return '%s%s' % (country, msisdn.lstrip('0'))

################
# Money format #
################
def should_int(value):
    int_ = int(value)
    if int_ == value:
        return int_
    return value

def thousand(value, float_count=None):
    if float_count is None: # autodetection
        if type(value) in (IntType, LongType):
            float_count = 0
        else:
            float_count = 2
    return locale.format('%%.%df' % float_count, value, True)

def money(value, float_count=None, currency=None):
    if value < 0:
        v = abs(value)
        format_ = '(%s)'
    else:
        v = value
        format_ = '%s'
    if currency is None:
        currency = locale.localeconv()['currency_symbol']
    s = ' '.join([currency, thousand(v, float_count)])
    return format_ % s

###########    
# Pyramid #
###########    
def get_settings():
    return get_current_registry().settings
    
def get_timezone():
    settings = get_settings()
    return pytz.timezone(settings['timezone'])

########    
# Time #
########
one_second = timedelta(1.0/24/60/60)
DateType = type(date.today())
DateTimeType = type(datetime.now())
TimeZoneFile = '/etc/timezone'
if os.path.exists(TimeZoneFile):
    DefaultTimeZone = open(TimeZoneFile).read().strip()
else:
    DefaultTimeZone = 'Asia/Jakarta'

def as_timezone(tz_date):
    localtz = get_timezone()
    if not tz_date.tzinfo:
        tz_date = create_datetime(tz_date.year, tz_date.month, tz_date.day,
                                  tz_date.hour, tz_date.minute, tz_date.second,
                                  tz_date.microsecond)
    return tz_date.astimezone(localtz)    

def create_datetime(year, month, day, hour=0, minute=7, second=0,
                     microsecond=0):
    tz = get_timezone()        
    return datetime(year, month, day, hour, minute, second,
                     microsecond, tzinfo=tz)

def create_date(year, month, day):    
    return create_datetime(year, month, day)
    
def create_now():
    tz = get_timezone()
    return datetime.now(tz)
    
def date_from_str(value):
    separator = None
    value = value.split()[0] # dd-mm-yyyy HH:MM:SS  
    for s in ['-', '/']:
        if value.find(s) > -1:
            separator = s
            break    
    if separator:
        t = map(lambda x: int(x), value.split(separator))
        y, m, d = t[2], t[1], t[0]
        if d > 999: # yyyy-mm-dd
            y, d = d, y
    else:
        y, m, d = int(value[:4]), int(value[4:6]), int(value[6:])
    return date(y, m, d)    
    
def dmy(tgl):
    if tgl:
        return tgl.strftime('%d-%m-%Y')
    return

def dmy_to_date(tgl):
    return datetime.strptime(tgl,'%d-%m-%Y').date()
    
def dmyhms(t):
    return t.strftime('%d-%m-%Y %H:%M:%S')

def ymd(tgl):
    if tgl:
        return tgl.strftime('%Y-%m-%d')
    return

def ymd_to_date(tgl):
    return datetime.strptime(tgl,'%Y-%m-%d').date()
    
def next_month(year, month):
    if month == 12:
        month = 1
        year += 1
    else:
        month += 1
    return year, month
    
def best_date(year, month, day):
    try:
        return date(year, month, day)
    except ValueError:
        last_day = calendar.monthrange(year, month)[1]
        return date(year, month, last_day)

def next_month_day(year, month, day):
    year, month = next_month(year, month)
    return best_date(year, month, day)
    
##########
# String #
##########
def one_space(s):
    s = s.strip()
    while s.find('  ') > -1:
        s = s.replace('  ', ' ')
    return s
    
def to_str(v):
    typ = type(v)
    if typ == DateType:
        return dmy(v)
    if typ == DateTimeType:
        return dmyhms(v)
    if v == 0:
        return '0'
    if typ in [UnicodeType, StringType]:
        return v.strip()
    elif typ is BooleanType:
        return v and '1' or '0'
    return v and str(v) or ''
    
def dict_to_str(d):
    r = {}
    for key in d:
        val = d[key]        
        r[key] = to_str(val)
    return r
    
def split(s, c=4):
    r = []
    while s:
        t = s[:c]
        r.append(t)
        s = s[c:]
    return ' '.join(r)
    
########    
# File #
########    
# http://stackoverflow.com/questions/2257441/random-string-generation-with-upper-case-letters-and-digits-in-python
def get_random_string():
    return ''.join(choice(ascii_uppercase + ascii_lowercase + digits) \
            for _ in range(6))
        
def get_ext(filename):
    return os.path.splitext(filename)[-1]
    
def file_type(filename):    
    ctype, encoding = mimetypes.guess_type(filename)
    if ctype is None or encoding is not None:
        ctype = 'application/octet-stream'
    return ctype    


class SaveFile(object):
    def __init__(self, dir_path):
        self.dir_path = dir_path

    # Unchanged file extension, and make file prefix unique with sequential
    # number.
    def create_fullpath(self, ext=''):
        while True:
            filename = get_random_string() + ext
            fullpath = os.path.join(self.dir_path, filename)
            if not os.path.exists(fullpath):
                return fullpath
        
    def save(self, content, filename=None):
        fullpath = create_fullpath()
        f = open(fullpath, 'wb')
        f.write(content)
        f.close()
        return fullpath
        
        
class Upload(SaveFile):
    def save(self, request, name):
        input_file = request.POST[name].file
        ext = get_ext(request.POST[name].filename)
        fullpath = self.create_fullpath(ext)
        output_file = open(fullpath, 'wb')
        input_file.seek(0)
        while True:
            data = input_file.read(2<<16)
            if not data:
                break
            output_file.write(data)
        output_file.close()
        return fullpath

class UploadFiles(SaveFile):
    def save(self, fs):
        input_file = fs.file
        ext = get_ext(fs.filename)
        fullpath = self.create_fullpath(ext)
        output_file = open(fullpath, 'wb')
        input_file.seek(0)
        while True:
            data = input_file.read(2<<16)
            if not data:
                break
            output_file.write(data)
        output_file.close()
        return fullpath    
        
class CSVRenderer(object):
   def __init__(self, info):
      pass

   def __call__(self, value, system):
      """ Returns a plain CSV-encoded string with content-type
      ``text/csv``. The content-type may be overridden by
      setting ``request.response.content_type``."""

      request = system.get('request')
      if request is not None:
         response = request.response
         ct = response.content_type
         if ct == response.default_content_type:
            response.content_type = 'text/csv'

      fout = io.BytesIO() #StringIO()
      fcsv = csv.writer(fout, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)
      #fcsv = UnicodeWriter(fout, delimiter=',', quotechar=',', quoting=csv.QUOTE_MINIMAL)
      #print value.get('header', [])
      fcsv.writerow(value.get('header', []))
      fcsv.writerows(value.get('rows', []))

      return fout.getvalue()    

# Data Table Function        
def _DTstrftime(chain):
    ret = chain and datetime.strftime(chain, '%d-%m-%Y')
    if ret:
        return ret
    else:
        return chain
        
def _DTnumber_format(chain):
    import locale
    locale.setlocale(locale.LC_ALL, 'id_ID.utf8')
    ret = locale.format("%d", chain, grouping=True)
    if ret:
        return ret
    else:
        return chain
                
def _DTupper(chain):
    ret = chain.upper()
    if ret:
        return ret
    else:
        return chain
        
def _DTstatus(chain):
    if chain:
        ret = 'Aktif'
    else:
        ret = 'Mati'
    if ret:
        return ret
    else:
        return chain
##########
# String #
##########
def clean(s):
    r = ''
    for ch in s:
        ascii = ord(ch)
        if ascii > 126 or ascii < 32:
            ch = ' '
        r += ch
    return r

def to_str(s):
    s = s or ''
    s = type(s) in [StringType, UnicodeType] and s or str(s)
    return clean(s)

def left(s, width):
    s = to_str(s)
    return s.ljust(width)[:width]

def right(s, width):
    s = to_str(s)
    return s.zfill(width)[:width]
    
##################
# Data Structure #
##################
class FixLength(object):
    def __init__(self, struct):
        self.set_struct(struct)

    def set_struct(self, struct):
        self.struct = struct
        self.fields = {}
        for s in struct:
            name = s[0]
            size = s[1:] and s[1] or 1
            typ = s[2:] and s[2] or 'A' # N: numeric, A: alphanumeric
            self.fields[name] = {'value': None, 'type': typ, 'size': size}

    def set(self, name, value):
        self.fields[name]['value'] = value

    def get(self, name):
        v = self.fields[name]['value']
        if v:
            return v.strip()
        return ''

    def __setitem__(self, name, value):
        self.set(name, value)

    def __getitem__(self, name):
        return self.get(name)

    def get_raw(self):
        s = ''
        for name, size, typ in self.struct:
            v = self.fields[name]['value']
            pad_func = typ == 'N' and right or left
            if v and typ == 'N':
                i = int(v)
                if v == i:
                    v = i
            s += pad_func(v, size)
        return s
        
    def get_raw_dotted(self):
        s = ''
        for name, size, typ in self.struct:
            v = self.fields[name]['value']
            pad_func = typ == 'N' and right or left
            if v and typ == 'N':
                i = int(v)
                if v == i:
                    v = i
            s += pad_func(v, size)
            s += "."
        return s[:-1]
        
    def set_raw(self, raw):
        awal = 0
        for t in self.struct:
            name = t[0]
            size = t[1:] and t[1] or 1
            akhir = awal + size
            value = raw[awal:akhir]
            if not value:
                return
            self.set(name, value)
            awal += size
        return True

    def from_dict(self, d):
        for name in self.fields:
            if name in d and d[name]:
                value = d[name]
                self.set(name, value)
                
        #changed 11 des 2016
        # for name in d:
            # value = d[name]
            # self.set(name, value)


    def to_dict(self):
        r = {}
        for name in self.fields:
            r[name] = self.get(name)
        return r

    def length(self):
        return len(self.get_raw())