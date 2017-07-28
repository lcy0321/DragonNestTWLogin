#! /usr/bin/python3
"""Directly login to Dragon Nest Taiwan without the webpages and the plug-ins."""

import re
import subprocess
import webbrowser
import xml.etree.ElementTree as ET
from codecs import decode, encode
from configparser import ConfigParser
from getpass import getpass

import requests
from bs4 import BeautifulSoup

INI_FILENAME = 'account.ini'
VCODE_PNG_FILENAME = 'vcode.png'
GAME_FOLDER_LOC = r'C:\Program Files (x86)\GF\DragonNest'
LOGIN_URL = r'https://gf2.gameflier.com/game_zone/dn/dn_login.aspx'
VCODE_URL = r'https://gf2.gameflier.com/VCode/spic.aspx?w=80&h=26'
START_URL = r'http://gf2.gameflier.com/func/gameStart2.aspx?Game=dn'

PATCH_CONFIG_URL = r'http://dnpatch.gameflier.com/PatchConfigList.xml'
"""The official login site redirect to non-HTTPS URL"""

PATCH_URL = r'http:\\dnpatch.gameflier.com''\\'
"""It is the orginal format used by launcher."""

def _check_account_name_format(account_name):
    """ Check the input email account .
        It should be validated as same as on the official login page. """
    if not account_name:
        return False

    account_format = r'^([\w\-\.]+)' \
                     r'@((\[[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\.)|' \
                     r'(([\w-]+\.)+))([a-zA-Z]{2,4}|' \
                     r'[0-9]{1,3})(\]?)$'

    return bool(re.match(account_format, account_name))

def _check_password_format(password):
    """ Check the input password.
        It should be validated as same as on the official login page. """
    if not password:
        return False

    # the length of the password should between 6 and 12
    if not 6 <= len(password) <= 12:
        return False

    invalid_characters = r'[^a-z0-9A-Z]'

    return not re.search(invalid_characters, password)

def _get_account_name_from_input():
    while True:
        account_name = input("Email Account> ").strip()
        if _check_account_name_format(account_name):
            return account_name
        else:
            print('ERROR: Invalid email address.')

def _get_password_from_input():
    while True:
        password = getpass("Password> ").strip()
        if _check_password_format(password):
            return password
        else:
            print('ERROR: Invalid password.')

def _encode_password(pass_str):
    """encode the pass_str"""
    return encode(pass_str.encode(), 'base64').decode()

def _decode_password(pass_str):
    """decode the pass_str"""
    return decode(pass_str.encode(), 'base64').decode()

def get_account_from_ini(ini_filename):
    """Get account name and password from the ini file"""
    account = ConfigParser(interpolation=None)
    if not (account.read(ini_filename) and account.has_section('Account')):
        user_account = _get_account_name_from_input()
        user_password = _get_password_from_input()
        password_saved = input("Save password?[Y/N]> ").strip().lower() == 'y'

        account.add_section('Account')
        account.set('Account', 'user_account', user_account)
        account.set(
            'Account',
            'user_password',
            _encode_password(user_password)
            if password_saved is True
            else ''
        )
        account.set('Account', 'password_saved', str(password_saved))

        with open(ini_filename, 'w') as ini_file:
            account.write(ini_file)

        return {'user_account': user_account,
                'user_password': user_password}
    return {
        'user_account':
            account.get('Account', 'user_account'),
        'user_password':
            _decode_password(account.get('Account', 'user_password'))
            if account.getboolean('Account', 'password_saved') is True
            else _get_password_from_input()
    }

def get_login_token(account):
    """Get the token from the login page with the given account dict."""
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
        with open(VCODE_PNG_FILENAME, 'wb') as vcode_png_file:
            vcode_png_file.write(vcode_res.content)
        webbrowser.open(VCODE_PNG_FILENAME)
        tbv_code = input('vcode: ').strip()

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

def get_patch_config():
    """Get ip, port from patch server, get ver from file"""
    req = requests.get(PATCH_CONFIG_URL)
    if req.status_code != requests.codes.ok:   #pylint: disable=no-member
        print('Cannot get PatchConfigList.xml!')
        print('Status Code: ' + req.status_code)
        return
    req.encoding = 'utf-8-sig'
    xml = ET.XML(req.text)
    xml = xml.find('./ChannelList/Local[@local_name]')
    xml_ip = xml.findall('./login')
    server_ip = xml_ip[0].get('addr') + ';' + xml_ip[1].get('addr')
    port = xml_ip[0].get('port') + ';' + xml_ip[1].get('port')

    with open(GAME_FOLDER_LOC + r'\Version.cfg', 'r') as ver_file:
        ver = re.search('Version +([0-9]+)', ver_file.readline()).group(1)

    return {'ip': server_ip, 'port': port, 'ver': ver}

def login(token, patch_config):
    """Open DragonNest with the given token string."""
    # Open DNLauncher.exe
    # subprocess.Popen(
    #     [GAME_FOLDER_LOC + r'\dnlauncher.exe', token],
    #     cwd=GAME_FOLDER_LOC
    # )

    subprocess.Popen(
        [
            GAME_FOLDER_LOC + r'\DragonNest.exe',
            '/logintoken:' + token,
            '/ip:' + patch_config['ip'],
            '/port:' + patch_config['port'],
            '/Lver:2',
            '/use_packing',
            '/gamechanneling:0',
            '/patchver:' + patch_config['ver'],
            '/patchurl:' + PATCH_URL
        ],
        cwd=GAME_FOLDER_LOC
    )

# def _test():
#     """For test"""
#     account_info = get_account_from_ini(INI_FILENAME)
#     token = get_login_token(account_info)
#     patch_config = get_patch_config()

#     print(account_info)
#     print(token)
#     print(patch_config)

def main():
    """Get account data, get token, and then login"""
    account_info = get_account_from_ini(INI_FILENAME)
    token = get_login_token(account_info)
    patch_config = get_patch_config()
    if token != None and patch_config != {}:
        login(token, patch_config)

if __name__ == '__main__':
    main()
    # _test()
