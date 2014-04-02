#!/usr/env/bin bash

# This script installs Python 3.4, then installs the chat server. Use it only
# if you really have no idea how python works; you'd be much better off
# creating a virtualenv and using that instead

echo "Checking for Python 3.4"

if which python3.4
then
    echo "Found Python 3.4"
    
else
    echo "No python 3.4 found. Installing..."
    
    echo "Adding repo"
    sudo add-apt-repository -y ppa:fkrull/deadsnakes
    
    echo "Updating"
    sudo apt-get -y update
    
    echo "Install Python"
    sudo apt-get -y install python3.4
fi

echo "Installing chat server"

sudo python3.4 ./setup.py install
