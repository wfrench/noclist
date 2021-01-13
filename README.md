NOCLIST Demo
===================

Code sample for noclist homework 

Build Instructions
==================
    git clone git@github.com:wfrench/noclist.git
    docker build -t noclist_script

Execution
=============

Tests
------------------
    # Run all tests
    docker run noclist_script pytest

    # Run all tests with editable source
    docker run -v `pwd`:/src noclist_script pytest

Process
---------------
    # Run the simulator either in another shell or backgrounded.  
    # TODO: Docker compose to improve this 
    docker run --rm -p 8888:8888 adhocteam/noclist

    # Run the script
    docker run --net="host" noclist_script    
    