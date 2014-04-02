NPproject3
==========

A chat server.

Installation Notes
------------------

This project is written in Python 3.4, and will require you to install Python 3.4 on your machine before you can run it. The easiest way to install Python 3.4 on Ubuntu 12.04 is via the Felix Krull deadsnakes repository. To install, run:

    sudo add-apt-repository -y ppa:fkrull/deadsnakes
    sudo apt-get update
    sudo apt-get -y install python3.4

Once python3.4 is installed, you can run the chat server. You have a number of different options. The server is shipped with a standard setup.py, meaning you can install it globally to your system or locally to a virtualenv. You can also just run the main module, making sure that you've set your `PYTHONPATH` correctly.

- For all run variants, first make sure to navigate to the root directory of the project (the one with `setup.py`) in it.
- To install globally:
    1. Run:
    
    sudo python3.4 setup.py install
    
    2. If installation completed successfully, you can now run `chat_server` or `npchat_server` at the shell:
    
    chat_server [args]

- To install to a virtualenv:
    1. Create the virtualenv:
    
    python3.4 -m venv ./env
    
    2. Activate the virtualenv:
    
    source env/bin/activate
    
    3. Install. No sudo is needed because it is being installed to a local directory.
    
    python3.4 setup.py
    
    4. If the installation completed successfully, you can now run `chat_server` or `npchat_server` at the shell:
    
    chat_server [args]

- To just run:

    1. Create a virtualenv
   
    python3.4 -m venv ./env
    
    2. Activate the virtualenv
    
    source env/bin/activate
    
    3. Run the main module:
    
    python3.4 -m npchat.server.main [args]

Running Notes
-------------

No matter how you run the server, you pass it args normally. You can use the -h option to see a summary of the usage. Here is a detailed summary of the available options:

- `-h` `--help` Display a usage message and exit.
- `-v` `--verbose` Display verbose output, as specified by the project. Proffessor Goldschmidt said in his office hours that the output format does not have to match that on the website exactly, and mine doesn't- it displays the `RCVD from` lines every time data is recieved, either as a line or a fixed-size block, rather than reading a whole message, parsing it, THEN outputting it verbosely.
- `-d` `--debug` Enable debug prints. While the `-v` option enables verbose prints, which are emitted every time data is sent or recieved, this option enables prints for other events: Server begins listening, TCP connection established, messages are sent. It works alongside `-v`, but is much less verbose overall, especially with many connected clients.
- `-e MESSAGE1 [MESSAGE2...]` `--extra MESSAGE1 [MESSAGE2...]` Extra messages. Each of this option's arguments are added as additional random messages that can be injected when the server sends random messages to clients.
- `-r RATE` `--rate RATE` Set a different random rate. Set the number of normal messages that will be sent between each random message. Set to 0 to disable all random messages.
- `-E` `--exclude` Disable the default random messages. If this option is given along with `-e`, only the messages given to `-e` will be candidates for random messages. If no `-e` is given, then this option disables random messages entirely.
- `-m` `--multiverse` Enable multiverse mode. In multiverse mode, each port is its own chat "universe-" each maintains a separate set of logged in clients, and those clients can only communicate with clients in the same universe (though UDP and TCP can still communicate with each other
- `-t SECONDS` `--timeout SECONDS` Set the client timeout. Clients (TCP or UDP) that don't send any data within this time frame will be logged out and disconnected

Add the port(s) after the options. Press ^C to terminate the server.

    
    
