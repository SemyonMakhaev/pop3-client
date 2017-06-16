# POP3-client

This program is for taking the information about
letters from a mail server using POP3 protocol.

The program uses port 110 for usual connection and
995 for ssl.

The program requires following arguments:

address - POP3 mail server IP-address
port - mail server port
login - user login
password - user password

-s, --start - the start index of letters range. Default value is 1
-e, --end - the last index of letters range

If the last index has not been set program supposes it (s + 1)
where s is the start index.

For each of loaded letters program saves the information.

To show a help message use -h or --help argument.
