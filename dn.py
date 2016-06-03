'''Directly login to DragonNest without webpage and plug-ins'''
from __future__ import print_function
import getpass
import subprocess
import webbrowser
import ConfigParser

import requests
from bs4 import BeautifulSoup

INI_FILENAME = 'account.ini'
VCODE_PNG_FILENAME = 'vcode.png'
GAME_FOLDER_LOC = r'C:\Program Files (x86)\GF\DragonNest'
LOGIN_URL = 'https://gf2.gameflier.com/game_zone/dn/dn_login.aspx'
VCODE_URL = 'https://gf2.gameflier.com/VCode/spic.aspx?w=80&h=26'
START_URL = 'http://gf2.gameflier.com/func/gameStart2.aspx?Game=dn'

def encode_password(pass_str):
    '''encode the pass_str'''
    return pass_str.encode('base64').encode('rot13')

def decode_password(pass_str):
    '''decode the pass_str'''
    return pass_str.decode('rot-13').decode('base64')

def get_account_from_ini(ini_filename):
    '''Get account name and password from the ini file'''
    account = ConfigParser.RawConfigParser()
    if not (account.read(ini_filename) and account.has_section('Account')):
        user_account = raw_input("Account> ")
        user_password = getpass.getpass("Password> ")
        password_saved = raw_input("Save password?[Y/N]> ").lower() == 'y'

        account.add_section('Account')
        account.set('Account', 'user_account', user_account)
        account.set(
            'Account',
            'user_password',
            encode_password(user_password)
            if password_saved is True
            else ''
        )
        account.set('Account', 'password_saved', password_saved)
        account.write(open(ini_filename, 'wb'))

        return {'user_account': user_account,
                'user_password': user_password}
    return {
        'user_account':
            account.get('Account', 'user_account'),
        'user_password':
            decode_password(account.get('Account', 'user_password'))
            if account.getboolean('Account', 'password_saved') is True
            else getpass.getpass("Password> ")
    }

def dragonnest_get_token(account):
    '''Get the token from the login page with the given account dict.'''
    session = requests.Session()
    start_res = session.get(LOGIN_URL)

    if start_res.status_code != requests.codes.ok:   #pylint: disable=no-member
        print('Cannot connect to login page!')
        print('Status Code: ' + start_res.status_code)
        return

    soup = BeautifulSoup(start_res.text, 'html.parser')
    view_state = soup.select('#__VIEWSTATE')[0]['value']
    view_state_generator = soup.select('#__VIEWSTATEGENERATOR')[0]['value']
    event_validation = soup.select('#__EVENTVALIDATION')[0]['value']

    tbv_code = ''
    while tbv_code == '':
        vcode_res = session.get(VCODE_URL)
        vcode_png_file = open(VCODE_PNG_FILENAME, 'wb')
        vcode_png_file.write(vcode_res.content)
        vcode_png_file.close()
        webbrowser.open(VCODE_PNG_FILENAME)
        tbv_code = raw_input('vcode: ')

    params = {
        '__VIEWSTATE': view_state,
        '__VIEWSTATEGENERATOR': view_state_generator,
        '__EVENTVALIDATION': event_validation,
        'UserAccount': account['user_account'],
        'UserPassword': account['user_password'],
        'TBVcode': tbv_code
    }
    headers = {
        'Host': 'gf2.gameflier.com',
        'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; WOW64; rv:45.0)'
                      'Gecko/20100101 Firefox/45.0',
        'Content-Type': 'application/x-www-form-urlencoded',
        'Accept': 'text/html,application/xhtml+xml,application/'
                  'xml;q=0.9,*/*;q=0.8',
        'Accept-Language': 'zh-TW,zh;q=0.8,en-US;q=0.5,en;q=0.3',
        'Accept-Encoding': 'gzip, deflate, br',
        'Referer': 'https://gf2.gameflier.com/game_zone/dn/dn_login.aspx'
    }

    login_res = session.post(
        'https://gf2.gameflier.com/game_zone/dn/dn_login.aspx',
        data=params,
        headers=headers
    )

    if login_res.url != START_URL:
        print('Login failed!')
        if login_res.url == LOGIN_URL:
            #Login failed and the page contains error message
            print(login_res.text[0:login_res.text.find('\n')])
            return

    soup = BeautifulSoup(login_res.text, 'html.parser')
    return soup.select('input[name="token"]')[0]['value']

def dragonnest_login(game_folder_loc, token):
    '''Open DragonNest with the given token string.'''
    subprocess.Popen(
        [game_folder_loc + r'\dnlauncher.exe', token],
        cwd=game_folder_loc
    )

def main():
    '''Get account data, get token, and then login'''
    account = get_account_from_ini(INI_FILENAME)
    token = dragonnest_get_token(account)
    if token != None:
        dragonnest_login(GAME_FOLDER_LOC, token)

if __name__ == '__main__':
    main()
