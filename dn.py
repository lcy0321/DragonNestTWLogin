import Cookie
import urllib
import getpass
import httplib
import subprocess
import webbrowser
import ConfigParser
from bs4 import BeautifulSoup

account = ConfigParser.RawConfigParser()

if not (account.read('account.ini') and account.has_section('Account')):
    account.add_section('Account')
    account.set('Account', 'user_account', raw_input("Account> "))
    account.set('Account', 'user_password', getpass.getpass("Password> "))
    account.write(open('account.ini', 'wb'))

user_account = account.get('Account', 'user_account')
user_password = account.get('Account', 'user_password')

conn = httplib.HTTPConnection('gf2.gameflier.com')
conn.request('GET', '/game_zone/dn/dn_login.aspx')
res = conn.getresponse()

if res.status != 200:
    print('Cannot connect to login page!')
    print('Status Code: ' + res.status)
    exit()

login_html = res.read().decode("utf-8")
soup = BeautifulSoup(login_html, 'html.parser')
view_state = soup.select('#__VIEWSTATE')[0]['value']
view_state_generator = soup.select('#__VIEWSTATEGENERATOR')[0]['value']
event_validation = soup.select('#__EVENTVALIDATION')[0]['value']
tbv_code = ''

conn = httplib.HTTPConnection('gf2.gameflier.com')
conn.request('GET', '/VCode/spic.aspx?w=80&h=26')
pic_res = conn.getresponse()
cookies = pic_res.getheader('Set-Cookie')

png_file = open('vcode.png', 'wb')
png_file.write(pic_res.read())
png_file.close()
webbrowser.open('vcode.png')

tbv_code = raw_input('vcode: ')
#user_password = raw_input('password: ')

params = urllib.urlencode({'__VIEWSTATE': view_state,
                           '__VIEWSTATEGENERATOR': view_state_generator,
                           '__EVENTVALIDATION': event_validation,
                           'UserAccount': user_account,
                           'UserPassword': user_password,
                           'TBVcode': tbv_code
                          })

headers = {'Host': 'gf2.gameflier.com',
           'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; WOW64; rv:45.0) Gecko/20100101 Firefox/45.0',
           'Content-Type': 'application/x-www-form-urlencoded',
           'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
           'Accept-Language': 'zh-TW,zh;q=0.8,en-US;q=0.5,en;q=0.3',
           'Accept-Encoding': 'gzip, deflate, br',
           'Referer': 'https://gf2.gameflier.com/game_zone/dn/dn_login.aspx',
           'Cookie': Cookie.SimpleCookie(cookies).output('value', '', ';'), 
           'Connection': "keep-alive"
          }

conn = httplib.HTTPConnection('gf2.gameflier.com')
conn.request('POST', '/game_zone/dn/dn_login.aspx', params, headers)
open_res = conn.getresponse()
start_cookies = cookies + ', ' + open_res.getheader('Set-Cookie')
open_html = open_res.read().decode("utf-8")

if open_res.getheader('Location') != '/func/gameStart.aspx?Game=dn':
    print('login failed!')
    print(open_html[0:open_html.find('\n')])
    exit()

start_headers = {'Host': 'gf2.gameflier.com',
                 'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; WOW64; rv:45.0) Gecko/20100101 Firefox/45.0',
                 'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                 'Accept-Language': 'zh-TW,zh;q=0.8,en-US;q=0.5,en;q=0.3',
                 'Accept-Encoding': 'gzip, deflate, br',
                 'Cookie': Cookie.SimpleCookie(start_cookies).output('value', '', ';')
                }
conn = httplib.HTTPConnection('gf2.gameflier.com')
conn.request('GET', '/func/gameStart2.aspx?Game=dn', None, start_headers)
start_res = conn.getresponse()
start_html = start_res.read().decode("utf-8")
soup = BeautifulSoup(start_html, 'html.parser')
token = soup.select('input[name="token"]')[0]['value']

subprocess.Popen(['C:\Program Files (x86)\GF\DragonNest\dnlauncher.exe', token], cwd = 'C:\Program Files (x86)\GF\DragonNest')