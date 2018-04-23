'''
    Created on 2014-11-09

    @author: Rodolfo Andrade

    Connect.py - Contains the Connect class that contains the basic method to login, logout and do get post request to a
    server such as Quality Center or Jira
'''

__author__ = 'Rodolfo Andrade'

import sys

import requests
from requests.auth import HTTPBasicAuth

import logging

logger = logging.getLogger('QCRest')

debug = False

# Class that abstracts some of the configurations needed to connect to rest API namely the login, logout and
# other configurations such as the proxy
class Connect(object):
    # Initialize connection
    def __init__(self, url_login, url_logout, silent=False, session=None, proxies=None):

        # Define if function in class should exit silently or raise exception
        self.silent = silent

        # If session does not exist create one
        if session is None:
            session = requests.Session()

        self.session = session

        # Initialize proxies
        if proxies is None:
            proxies = {'http': None, 'https': None}
        self.proxies = proxies

        # Define url for login
        if url_login == '':
            self.url_login = None
        else:
            self.url_login = url_login

        # Define url for logout
        if url_logout == '':
            self.url_logout = None
        else:
            self.url_logout = url_logout

    # Login function that uses HTTPBasicAuth
    def login(self, user=None, passwd=None, **kwargs):

        # If no login url is defined, do nothing
        if self.url_login is None and debug:
            print ('login: url not defined... doing nothing... ')
            return None

        # Validate input parameters
        if self.url_login is None:
            print ('login: url - ' + str(self.url_login) + ' is not valid!')
        if user is None:
            print ('login: user - ' + str(user) + ' is not valid!')
        if passwd is None:
            print ('login: passwd - ' + str(passwd) + ' is not valid!')

        # Login
        # self.debuginfo("login: URL: ", self.url_login)
        # self.debuginfo("login: Proxy: ", self.proxies)
        # self.debuginfo("login: User: ", user)
        # self.debuginfo("login: Pass: ", passwd)

        if debug:
            sys.stdout.write('login: Logging user \'' + str(user) + '\' using \'' + str(self.url_login) + '\'...')
        r = self.get(self.url_login, auth=HTTPBasicAuth(user, passwd), **kwargs)

        # Validate response code
        self._validateResponse(r, 'login')

        return r

    # Logout function
    def logout(self, **kwargs):

        # If no logout url is defined, do nothing
        if self.url_logout is None and debug:
            print ('logout: url not defined... doing nothing... ')
            return None

        # Logout
        # self.debuginfo("logout: URL: ", self.url_logout)
        # self.debuginfo("logout: Proxy: ", self.proxies)

        if debug:
            sys.stdout.write('logout: Logging out using \'' + str(self.url_logout) + '\'...')

        r = self.get(self.url_logout, **kwargs)

        # Validate response code
        self._validateResponse(r, 'logout')

        return r

    # Get a specific url
    def get(self, url, **kwargs):

        req = self.session.get(url, proxies=self.proxies, **kwargs)

        return req

    # Post a specific url
    def post(self, url, **kwargs):

        req = self.session.post(url, proxies=self.proxies, **kwargs)

        return req

    # Put a specific url
    def put(self, url, **kwargs):

        req = self.session.put(url, proxies=self.proxies, **kwargs)

        return req

    # Delete a specific url
    def delete(self, url, **kwargs):

        req = self.session.delete(url, proxies=self.proxies, **kwargs)

        return req

    # Auxiliar function to print debug info
    @staticmethod
    def debuginfo(message, value):

        logger.debug(message + ': ' + str(value))

    # Validate http response and act according
    def _validateResponse(self, response, function='None', expected_response_code=200, debug=debug):

        # Validate response code
        if response.status_code == expected_response_code:

            if debug:
                logger.debug(' OK! (' + str(response.status_code) + ')')
        else:

            if debug:
                logger.debug(' Ups something went wrong! (' + str(response.status_code) + '). Details follow:\n' +
                      response.text + '\n')

            # Slient exit?
            if not self.silent:
                raise ConnectionError('Status code != ' + str(expected_response_code)
                                      + ' (' + str(response.status_code) + ')', function
                                      + ': The status code is not the expected! Details follow:\n'
                                      + response.text + '\n')


# Class to handle specific errors when using class connect
class ConnectionError(Exception):
    """Exception raised for errors in the connection

    Attributes:
    expr -- input expression in which the error occurred
    msg  -- explanation of the error
    """

    def __init__(self, expr, msg):
        self.expr = expr
        self.msg = msg

