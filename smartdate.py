# -*- coding: utf-8 -*-
from datetime import datetime, timedelta
import string

tokens = (
	'SPECIAL',
	'CLOSEST',
	'MONTH',
	'DAY_OF_WEEK',
	'TIME_OF_DAY',
	'NUMBER',
	'DASH',
	'PLUS',
	'SLASH',
	'COMMA',
	'COLON',
	'DOT',
	'AT',
	'UTC',
	'YEARS',
	'MONTHS',
	'WEEKS',
	'FORTNIGHTS',
	'DAYS',
	'HOURS',
	'MINUTES',
	'SECONDS',
	'PAST'
)

t_SPECIAL = r'now|today|tomorrow|yesterday'
t_CLOSEST = r'next|last'
t_MONTH = r'january|jan|february|feb|march|mar|april|apr|may|june|jun|july|jul|august|aug|september|sep|sept|october|oct|november|nov|december|dec'
t_DAY_OF_WEEK = r'monday|mon|tuesday|tue|wednesday|wed|wednes|thursday|thur|thurs|friday|fri|saturday|sat|sunday|sun'
t_TIME_OF_DAY = r'am|pm|p\.m\.|a\.m\.'
t_NUMBER = r'\d+'
t_DASH = r'-'
t_PLUS = r'\+'
t_SLASH = r'/'
t_COMMA = r','
t_COLON = r':'
t_DOT = r'\.'
t_AT = r'@'
t_UTC = r'utc|z'
t_YEARS = r'years|year'
t_MONTHS = r'months|month'
t_WEEKS = r'weeks|week'
t_FORTNIGHTS = r'fortnights|fortnight'
t_DAYS = r'days|day'
t_HOURS = r'hours|hour'
t_MINUTES = r'minutes|minute'
t_SECONDS = r'seconds|second'
t_PAST = r'ago'

t_ignore = string.whitespace

def t_error(t):
	raise SyntaxError("Illegal character '%s'" % t.value[0])

import ply.lex as lex
lex.lex()

today = lambda: datetime.now().replace(hour=0,minute=0,second=0,microsecond=0)

def year_short_to_long(year):
	if year > 69:
		return 1900 + year
	else:
		return 2000 + year

def hour_to_24(hour, pm):
	if hour < 12 and pm:
		hour += 12
	elif hour == 12 and not pm:
		hour = 0
	elif hour > 12 and pm:
		raise ValueError("am/pm cannot be used with 24-hour time")
	return hour

weekday_index = {
	'monday':0,'mon':0,
	'tuesday':1,'tue':1,
	'wednesday':2,'wed':2,'wednes':2,
	'thursday':3,'thur':3,'thurs':3,
	'friday':4,'fri':4,
	'saturday':5,'sat':5,
	'sunday':6,'sun':6,
}

month_index = {
	'january':1,'jan':1,
	'february':2,'feb':2,
	'march':3,'mar':3,
	'april':4,'apr':4,
	'may':5,
	'june':6,'jun':6,
	'july':7,'jul':7,
	'august':8,'aug':8,
	'september':9,'sep':9,'sept':9,
	'october':10,'oct':10,
	'november':11,'nov':11,
	'december':12,'dec':12,
}

def p_all(p):
	'''value : datetime
			| timedelta
	'''
	p[0] = p[1]

def p_date_or_time_only(p):
	'''datetime : date
				| time'''
	p[0] = p[1]

def p_date_time(p):
	'''datetime : date time'''
	t = p[2]
	p[0] = p[1].replace(hour=t.hour, minute=t.minute, second=t.second,microsecond=t.microsecond,tzinfo=t.tzinfo)

def p_time_utc(p):
	'''time : time PLUS NUMBER
			| time DASH NUMBER
			| time UTC PLUS NUMBER
			| time UTC DASH NUMBER
	'''
	tm = p[1]
	if p[2] == '+' or p[2] == '-':
		offset = int(p[2]+p[3])
	else:
		offset = int(p[3]+p[4])
	p[0] = p[1]

def p_time_tod(p):
	'''time : time TIME_OF_DAY'''
	p[0] = p[1].replace(hour=hour_to_24(p[1].hour, p[2] == 'pm' or p[2] == 'p.m.'))

def p_time_epoch(p):
	'''time : AT NUMBER'''
	p[0] = datetime.fromtimestamp(int(p[2]))

def p_time_H(p):
	'''time : NUMBER TIME_OF_DAY'''
	p[0] = today().replace(hour=hour_to_24(int(p[1]), p[2] == 'pm' or p[2] == 'p.m.'))

def p_time_HM(p):
	'''time : NUMBER COLON NUMBER'''
	t = today()
	p[0] = t.replace(hour=int(p[1]), minute=int(p[3]))

def p_time_HMS(p):
	'''time : NUMBER COLON NUMBER COLON NUMBER'''
	t = today()
	p[0] = t.replace(hour=int(p[1]), minute=int(p[3]), second=int(p[5]))

def p_time_HMSu(p):
	'''time : NUMBER COLON NUMBER COLON NUMBER DOT NUMBER'''
	t = today()
	p[0] = t.replace(hour=int(p[1]), minute=int(p[3]), second=int(p[5]), microsecond=int(p[7]))

def p_special(p):
	'''date : SPECIAL'''
	if p[1] == 'now':
		p[0] = datetime.now()
	else:
		p[0] = today()
		if p[1] == 'tomorrow':
			p[0] += timedelta(days=1)
		elif p[1] == 'yesterday':
			p[0] -= timedelta(days=1)

def p_closest(p):
	'''date : CLOSEST DAY_OF_WEEK'''
	t = today()
	diff = weekday_index[p[2]] - t.weekday()
	if diff < 0 and p[1] == 'next':
		diff += 7
	elif diff > 0 and p[1] == 'last':
		diff -= 7
	
	p[0] = t + timedelta(days=diff)

def p_dashed(p):
	'''date : NUMBER DASH NUMBER DASH NUMBER'''
	year = int(p[1])
	if len(p[1]) == 2:
		year = year_short_to_long(year)
	
	p[0] = datetime(year=year, month=int(p[3]), day=int(p[5]))

def p_common_us(p):
	'''date : NUMBER SLASH NUMBER SLASH NUMBER'''
	year = int(p[5])
	if len(p[5]) == 2:
		year = year_short_to_long(year)
	
	p[0] = datetime(year=year, month=int(p[1]), day=int(p[3]))

def p_month_written(p):
	'''date : NUMBER MONTH NUMBER
		 | NUMBER DASH MONTH DASH NUMBER
	'''
	day = int(p[1])
	if p[2] == '-':
		month = p[3]
		year = p[5]
	else:
		month = p[2]
		year = p[3]
	month = month_index[month]
	
	if len(year) == 2:
		year = year_short_to_long(int(year))
	else:
		year = int(year)
	
	p[0] = datetime(year=year, month=month, day=day)

def p_month_first(p):
	'''date : MONTH NUMBER COMMA NUMBER'''
	year = int(p[4])
	if len(p[4]) == 2:
		year = year_short_to_long(year)
	p[0] = datetime(year=year, month=month_index[p[1]], day=int(p[2]))

def p_month_only(p):
	'''date : MONTH NUMBER'''
	p[0] = datetime(year=today().year, month=month_index[p[1]], day=int(p[2]))

def p_ago(p):
        '''timedelta : timedelta PAST'''
        p[0] = -p[1]

def p_years(p):
        '''timedelta : NUMBER YEARS'''
        p[0] = timedelta(years=int(p[1]))

def p_months(p):
        '''timedelta : NUMBER MONTHS'''
        p[0] = timedelta(months=int(p[1]))

def p_weeks(p):
        '''timedelta : NUMBER WEEKS'''
        p[0] = timedelta(weeks=int(p[1]))

def p_fortnights(p):
        '''timedelta : NUMBER FORTNIGHTS'''
        p[0] = timedelta(days=14*int(p[1]))

def p_days(p):
        '''timedelta : NUMBER DAYS'''
        p[0] = timedelta(days=int(p[1]))

def p_hours(p):
        '''timedelta : NUMBER HOURS'''
        p[0] = timedelta(hours=int(p[1]))

def p_minutes(p):
        '''timedelta : NUMBER MINUTES'''
        p[0] = timedelta(minutes=int(p[1]))

def p_seconds(p):
        '''timedelta : NUMBER SECONDS'''
        p[0] = timedelta(seconds=int(p[1]))
	   
def p_error(t):
	raise SyntaxError("Syntax error at '%s'" % t.value)


import ply.yacc as yacc
yacc.yacc()


def parse(s):
	return yacc.parse(s.lower())
