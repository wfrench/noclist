""" Unit tests for the noclist script """
import json
import pytest
import logging
import requests
import noclist.request 
from unittest.mock import Mock
from noclist.request import Auth, User, FetchException, CHECKSUM_TOKEN_KEY

log = logging.getLogger()

####
# Test values
####
AUTHKEY="12345"
USER_CHECKSUM="c20acb14a3d3339b9e92daebb173e41379f9f2fad4aa6a6326a696bd90c67419"
CHECKSUM_TOKEN_KEY = "X-Request-Checksum"
AUTH_TOKEN_KEY = "Badsec-Authentication-Token"

USER_GOOD_RESPONSE = '''18207056982152612516
7692335473348482352
694423021435122566'''
USER_GOOD_RESULT = '["18207056982152612516", "7692335473348482352", "694423021435122566"]'

# Assuming this is a bad case. 
USER_BAD_RESPONSE = "Not a user list"

def test_request_properties():
    """ Verify our properties are working for the request """
    auth = Auth("foo")
    assert(auth.entrypoint == "auth")
    assert(auth.uri == "foo/auth")

def test_auth(mocker):
    """ Test that we can store an auth key poperly """ 
    mocker.patch.object(noclist.request.Auth, '_fetch', return_value=AUTHKEY)

    auth = Auth()
    assert(auth.token == AUTHKEY)

def test_auth_exception(mocker):
    """ Verify auth exceptions are happening and retry properly """
    mocker.patch.object(requests, 'get', side_effect=FetchException("mock exception"))

    auth = Auth()
    with pytest.raises(FetchException):
        auth.token()
    assert(auth._attempts == 3)

def test_checksum(mocker):
    """ Ensure our checksum properties work as expected """
    mocker.patch.object(noclist.request.Auth, '_fetch', return_value=AUTHKEY)

    user = User()
    assert(user.checksum == USER_CHECKSUM)

    auth = Auth()
    assert(auth.checksum is None)

def test_request_headers(mocker):
    """ Ensure our request headers are being sent for user objects """
    mocker.patch.object(noclist.request.Auth, '_fetch', return_value=AUTHKEY)
    user = User()
    assert(CHECKSUM_TOKEN_KEY in user._request_headers())

def test_user_list(mocker):
    """ Test that we can parse user list output """
    # Mock most of the request info so we can work the response handler
    mock = Mock()
    mock.text = USER_GOOD_RESPONSE
    mock.status_code = 200
    mocker.patch.object(requests, 'get', return_value=mock)
    mocker.patch.object(noclist.request.User, 'checksum', return_value=USER_CHECKSUM)
    user = User()

    assert(user.list() == USER_GOOD_RESULT)

    # Check for bad responses too
    mock.text = USER_BAD_RESPONSE
    mocker.patch.object(requests, 'get', return_value=mock)
    with pytest.raises(Exception):
        result = user.list()
    
