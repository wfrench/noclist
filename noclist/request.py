""" Defines all objects used to interact directly with the API

Defines User and Auth objects for interacting with the BADSEC
API.  All API interactions have a retry process built in and 
will raise a FetchException if the retry attempts are exausted. """

import json
import logging
import requests
import numpy as np
from retry import retry
from hashlib import sha256
from unittest.mock import Mock

log = logging.getLogger()

# Constants.  Should in in a config object
API_URI = "http://127.0.0.1:8888"
RETRY_COUNT = 3
RETRY_DELAY = 2
AUTH_TOKEN_KEY = "Badsec-Authentication-Token"
CHECKSUM_TOKEN_KEY = "X-Request-Checksum"

class FetchException(Exception): 
    """ Generic auth request exceptions we can used for retry """

class Request(object):
    """ Base class for fetching BADSEC data """
    def __init__(self, uri=API_URI):
        self._api_uri = uri
        self._attempts = 0
        self._entrypoint = None
        self._auth = None

    @property
    def entrypoint(self):
        """ Entry point into the api.  Must be set in derived classes """
        if self._entrypoint is None: 
            raise Exception("_entrypoint not set in derived class")
        return self._entrypoint

    @property
    def uri(self):
        """ URI for the request """
        return "%s/%s" % (self._api_uri, self._entrypoint)

    @property
    def checksum(self):
        """ BADSEC Checksum calculated with the auth token and entry point """
        if self._auth is None: 
            return None
        else: 
            auth_string = "%s/%s" % (self._auth.token, self._entrypoint)
            log.info("Building checksum from %s", auth_string)
            return sha256(auth_string.encode()).hexdigest()

    @retry(FetchException, tries=RETRY_COUNT, delay=RETRY_DELAY)
    def _fetch(self):
        """ Attempt to fetch from the entrypoint.  retry 3 times """
        try:
            error_message = None

            # TODO reset this retry counter upon total failure.  Could just wrap the fetch call
            self._attempts += 1
            headers = self._request_headers()
            log.info("Fetch: %s (attempt %d/%d)", self.uri, self._attempts, RETRY_COUNT)
            r = requests.get(self.uri, headers=headers)

            if r is None:
                error_message = "Request failed"

            elif r.status_code != 200: 
                error_message = "Response code not 200: %s" % r.status_code

            if error_message is not None:
                log.warning(error_message)
                raise FetchException(error_message)

            # Looks good so far.  Let's parse the results
            return self._fetch_handler(r)

        except requests.exceptions.ConnectionError as e:
            raise FetchException(str(e)) 

    def _fetch_handler(self, request):
        raise Exception("Must be derived in child class")

    def _request_headers(self): 
        """ return a dictionary with an auth header if needed """
        headers = None
        checksum = self.checksum
        if checksum is not None: 
            headers = { CHECKSUM_TOKEN_KEY: checksum }
            log.info("Sending headers %s", headers)
        return headers


class Auth(Request):
    """ Auth class for fetching and caching a BADSEC auth token """
    def __init__(self, uri=API_URI):
        Request.__init__(self, uri)
        self._entrypoint = "auth"
        self._auth_token = None

    @property
    def token(self):
        """ Return the BADSEC auth token.  Fetch and cache if we haven't done that yet """
        if self._auth_token is None: 
            self._auth_token = self._fetch()
            log.info("Caching auth token: %s", self._auth_token)
        return self._auth_token

    def _fetch_handler(self, request):
        """ Overload the default handler becasuse all we care about is the auth header line """
        log.info(request.headers)
        if AUTH_TOKEN_KEY in request.headers:
            return request.headers[AUTH_TOKEN_KEY]
        else: 
            raise FetchException("%s header not found in response" % AUTH_TOKEN_KEY)

class User(Request):
    """ User class for fetching BADSEC user info """
    def __init__(self, uri=API_URI): 
        Request.__init__(self, uri)
        self._entrypoint = "users"
        self._auth = Auth(uri)

    def _fetch_handler(self, request):
        """ Parse the response body.   64bit integers on each line.  
        raise an FetchException if we have bad content """
        result = request.text.splitlines(False)
        for n in result: 
            try:
                log.info(np.uint64(n))
            except Exception as e: 
                log.error("Found bad user id in response. %s", request.text)
                raise FetchException("Failed to retrive user ids")

        return json.dumps(result)

    def list(self): 
        """ Return a json encoded list of user ids """
        return self._fetch()
    