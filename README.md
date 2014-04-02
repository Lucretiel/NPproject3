NPproject3
==========

A chat server.

Installation Notes
------------------

This project is written in Python 3.4, and will require you to install Python 3.4 on your machine before you can run it. The easiest way to install Python 3.4 on Ubuntu 12.04 is via the Felix Krull deadsnakes repository. To install, run:

```shell
sudo add-apt-repository -y ppa:fkrull/deadsnakes
sudo apt-get update
sudo apt-get -y install python3.4
```

Once Python 3.4 is installed, you can run the chat server. You have a number of different options. The server is shipped with a standard `setup.py`, meaning you can install it globally to your system or locally to a virtualenv. This has the advantage of creating the `chat_server` binary specified in the project and placing it in your `$PATH` You can also just run the main module.

- For all run variants, first make sure to navigate to the root directory of the project (the one with `setup.py`) in it.
- To install globally:

```bash
sudo python3.4 setup.py install  # Install globally to system
chat_server [args]  # Run
```

- To install to a virtualenv:
    
```bash
python3.4 -m venv ./env  # Create the virtualenv
source env/bin/activate  # Activate the virtualenv
python3.4 setup.py       # Install
chat_server [args]       # Run
```

- To just run:

```bash
python3.4 -m npchat.server.main [args]  # Run the main module
```

Running Notes
-------------

No matter how you run the server, you pass it args normally. You can use the -h option to see a summary of the usage. Here is a detailed summary of the available options:

- `-h` `--help` Display a usage message and exit.
- `-v` `--verbose` Display verbose output, as specified by the project. Professor Goldschmidt said in his office hours that the output format does not have to match that on the website exactly, and mine doesn't- it displays the `RCVD from` lines every time data is received, either as a line or a fixed-size block, rather than reading a whole message, parsing it, THEN outputting it verbosely.
- `-d` `--debug` Enable debug prints. While the `-v` option enables verbose prints, which are emitted every time data is sent or received, this option enables prints for other events: Server begins listening, TCP connection established, messages are sent. It works alongside `-v`, but is much less verbose overall, especially with many connected clients.
- `-e MESSAGE1...` `--extra MESSAGE1...` Extra messages. Each of this option's arguments are added as additional random messages that can be injected when the server sends random messages to clients.
- `-r RATE` `--rate RATE` Set a different random rate. Set the number of normal messages that will be sent between each random message. Set to 0 to disable all random messages.
- `-E` `--exclude` Disable the default random messages. If this option is given along with `-e`, only the messages given to `-e` will be candidates for random messages. If no `-e` is given, then this option disables random messages entirely.
- `-m` `--multiverse` Enable multiverse mode. In multiverse mode, each port is its own chat "universe-" each maintains a separate set of logged in clients, and those clients can only communicate with clients in the same universe (though UDP and TCP can still communicate with each other).
- `-t SECONDS` `--timeout SECONDS` Set the client timeout. Clients (TCP or UDP) that don't send any data within this time frame will be logged out and disconnected.

Add the port(s) after the options. Press `^C` to terminate the server.

Testing Notes
-------------

In addition to the standard testing via `netcat` or `telnet`, you can perform multiuser load testing with the utility I wrote, call `test_client`. If you installed the chat server via `setup.py install`, then you can run it with `npchat_test_client`, otherwise, run `python3.4 -m npchat.test_client`. Here's a summary of the arguments you can pass it:

- `-h` `--help` Print a usage message and exit.
- `-e N`, `--extra N` The number of users to run.
- `-u USERNAME` `--users USERNAME` An extra named user. If given, the messages this user recieves will be formatted and printed to the screen.
- `-m MESSAGE1...` `--messages MESSAGE1...` Extra messages to send. These will be added to the built-in list of testing messages.
- `-a MIN_TIME MAX_TIME` `--alive MIN_TIME MAX_TIME` If given, this option controls how long the clients will be alive for. They will pick a random number of seconds between `MIN_TIME` and `MAX_TIME` before logging out. When the last client logs out, the `test_client` program will end normally. If this option is not given, the clients will run forever.

After options, give a hostname and any number of ports to connect to. Each client will select a random port to connect to from the ports given.

Grading Notes
-------------

In various office hours sessions with Professor Goldschmidt, he confirmed that the following behaviors are acceptable for the project:

- The use of Python 3.4.
- The use of `asyncio` in Python (ie, not using strictly low-level calls like `listen`, `accept`, `recv`, etc).
- Custom verbose output formatting.
    - Add port number to the sender/recipient line
    - Split `RCVD from` blocks- they are verbosly printed as they are read
- Simply reject UDP packets from an unrecognized source, without touching or logging out any users.
    - Instead simply wait for a UDP user to timeout.
- Sending broadcasts to UDP users.
- Sending chunked messages to UDP users, as long as all of the chunks fit in a single UDP datagram.
- Silently ignoring sends to a nonexistent user.
    - If you send to multiple users (`SEND from_user recipient1 recipient2`), only the logged in users will receive the message.
- Excess data on the action lines is ignored. Currently, the client data parser strips the directive (`SEND`, `BROADCAST`, etc) from the front of the line, then tokenizes the rest of the line by whitespace. The first token is the `from_user` and, the rest are taken as "command arguments," even though only SEND uses them.
- Random messages do not have a trailing newline
- The `WHO HERE` username list does not have a trainline newline

