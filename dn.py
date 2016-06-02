import getpass
import subprocess
import webbrowser
import ConfigParser
import requests
from bs4 import BeautifulSoup

INI_FILENAME = 'account.ini'
GAME_FOLDER_LOC = r'C:\Program Files (x86)\GF\DragonNest'

def DragonNestLogin(ini_filename, game_folder_loc):
    account = ConfigParser.ConfigParser()
    if not (account.read(ini_filename) and account.has_section('Account')):
        account.add_section('Account')
        account.set('Account', 'user_account', raw_input("Account> "))
        account.set('Account', 'user_password', getpass.getpass("Password> "))
        account.write(open(ini_filename, 'wb'))

    user_account = account.get('Account', 'user_account')
    user_password = account.get('Account', 'user_password')

    session = requests.Session()
    start_res = session.get('https://gf2.gameflier.com/game_zone/dn/dn_login.aspx')

    if start_res.status_code != requests.codes.ok:
        print('Cannot connect to login page!')
        print('Status Code: ' + start_res.status_code)
        return False

    start_html = start_res.text
    soup = BeautifulSoup(start_html, 'html.parser')
    view_state = soup.select('#__VIEWSTATE')[0]['value']
    view_state_generator = soup.select('#__VIEWSTATEGENERATOR')[0]['value']
    event_validation = soup.select('#__EVENTVALIDATION')[0]['value']

    vcode_res = session.get('https://gf2.gameflier.com/VCode/spic.aspx?w=80&h=26')

    png_file = open('vcode.png', 'wb')
    png_file.write(vcode_res.content)
    png_file.close()
    webbrowser.open('vcode.png')
    tbv_code = raw_input('vcode: ')

    params = ({'__VIEWSTATE': view_state,
               '__VIEWSTATEGENERATOR': view_state_generator,
               '__EVENTVALIDATION': event_validation,
               'UserAccount': user_account,
               'UserPassword': user_password,
               'TBVcode': tbv_code
              })
    login_headers = {'Host': 'gf2.gameflier.com',
                     'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; WOW64; rv:45.0)'
                                   'Gecko/20100101 Firefox/45.0',
                     'Content-Type': 'application/x-www-form-urlencoded',
                     'Accept': 'text/html,application/xhtml+xml,application/'
                               'xml;q=0.9,*/*;q=0.8',
                     'Accept-Language': 'zh-TW,zh;q=0.8,en-US;q=0.5,en;q=0.3',
                     'Accept-Encoding': 'gzip, deflate, br',
                     'Referer': 'https://gf2.gameflier.com/game_zone/dn/dn_login.aspx'
                    }

    login_res = session.post('https://gf2.gameflier.com/game_zone/dn/dn_login.aspx',
                             data=params,
                             headers=login_headers)

    if login_res.url != 'http://gf2.gameflier.com/func/gameStart2.aspx?Game=dn':
        print('Login failed!')
        if login_res.url == 'https://gf2.gameflier.com/game_zone/dn/dn_login.aspx':
            print login_res.text[0:login_res.text.find('\n')]
        return False

    soup = BeautifulSoup(login_res.text, 'html.parser')
    token = soup.select('input[name="token"]')[0]['value']
    subprocess.Popen([game_folder_loc + r'\dnlauncher.exe', token], cwd=game_folder_loc)
    return True

DragonNestLogin(INI_FILENAME, GAME_FOLDER_LOC)
