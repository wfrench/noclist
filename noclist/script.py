#!/usr/bin/env python

""" List all users ids in the BADSEC system

Usage: 

# Inside the container
noclist/script.py

# From docker
docker run -v `pwd`:/src --net="host" noclist_script python3 noclist/script.py
"""

import sys
from noclist.request import User

class Request(object):
    pass

def main():
    """ Main script entry point """
    try:
        user = User()
        print(user.list())
        return 0
    except Exception as e:
        log.error(e)
        return 1


if __name__ == '__main__':
    sys.exit(main())