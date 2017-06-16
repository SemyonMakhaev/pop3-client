#!/usr/bin/env python3
"""
The program for taking the information
about letters on mail server using POP3 protocol.
"""
import sys

from socket import socket, AF_INET, SOCK_STREAM, timeout
from argparse import ArgumentParser
from ssl import wrap_socket
from logging import warning, error
from os import linesep
from letter import Letter, CRLF


POP3_PORT = 110
POP3_PORT_SSL = 995

ENCODING = "windows-1251"
START_LETTER = 1
TIMEOUT = 10
SERVER_REPLY_BUFFER = 50


def main():
    """Requests sending and letters taking."""
    args = argument_parse()
    letters = get_letters((args.address, args.port), args.login, \
                        args.password, args.start, args.end)

    for let in letters:
        print(let)


def argument_parse():
    """Arguments parsing."""
    parser = ArgumentParser(prog="python3 pop3.py", \
        description="A tool for letters taking from a POP3-server.", \
        epilog="(c) Semyon Makhaev, 2016. All rights reserved.")
    parser.add_argument("address", type=str, help="Mail server IP-address.")
    parser.add_argument("port", type=int, help="Mail server port.")
    parser.add_argument("login", type=str, help="User login.")
    parser.add_argument("password", type=str, help="User password.")
    parser.add_argument("-s", "--start", type=int, default=START_LETTER, \
        help="The start index of letters range.")
    parser.add_argument("-e", "--end", type=int, help="The last index of letters range.")
    args = parser.parse_args()

    if args.end is None:
        args.end = args.start

    elif args.start > args.end:
        warning("Incorrect letters indices. Set default values.")
        args.start = START_LETTER
        args.end = START_LETTER

    if args.port < 0 or args.port > 65535:
        warning("Incorrect port. Set default value.")
        args.port = POP3_PORT_SSL# Using POP3 SSL TCP-port.

    return args


def get_letters(host_port, login, password, start, end):
    """Returns taken letters."""
    port = host_port[1]
    sock = socket(AF_INET, SOCK_STREAM)
    sock.settimeout(TIMEOUT)

    try:
        if port == POP3_PORT:
            sock.connect(host_port)
            data = sock.recv(4096)
            analyse_data(data, "+OK")
            send_data(sock, "stls", "+OK")
            ssl_sock = wrap_socket(sock)
            ssl_sock.settimeout(TIMEOUT)

        elif port == POP3_PORT_SSL:
            ssl_sock = wrap_socket(sock)
            ssl_sock.settimeout(TIMEOUT)
            ssl_sock.connect(host_port)
            data = ssl_sock.recv(4096)
            analyse_data(data, "+OK")

        else:
            error("Incorrect port")
            sys.exit(0)

        with ssl_sock:
            send_data(ssl_sock, "user {}".format(login), "+OK")
            send_data(ssl_sock, "pass {}".format(password), "+OK")
            send_data(ssl_sock, "stat", "+OK")

            for idx in range(start, end + 1):
                request = "retr {}{}".format(idx, CRLF)
                sys.stderr.write(request)
                ssl_sock.send(request.encode(ENCODING))
                reply = read_letter(ssl_sock)
                let = Letter(reply, idx)
                let.start()
                yield let

            quit_command = "quit{}".format(CRLF)
            ssl_sock.send(quit_command.encode(ENCODING))
            sys.stderr.write(quit_command)

    except timeout:
        error("Connection time limit exceeded.")

    finally:
        sock.close()


def read_letter(sock):
    """Reads a letter from the socket."""
    buff = bytes()

    while True:
        data = sock.recv(512)
        if data.endswith("{0}.{0}".format(CRLF).encode(ENCODING)):
            break
        buff += data

    return buff


def send_data(sock, data, expected, profile=True):
    """Sends data to a given socket."""
    sock.send((data + CRLF).encode(ENCODING))

    if profile:
        sys.stderr.write(data + linesep)

    buff = sock.recv(4096)
    analyse_data(buff, expected)


def analyse_data(data, expected):
    """Checks that the server has sent an expected data."""
    data = data.decode(ENCODING)

    if not data.startswith(expected):
        if len(data) > SERVER_REPLY_BUFFER:
            data = data[:SERVER_REPLY_BUFFER] + "..."
        error("Unexpected server answer: %s%s", linesep, data)
        sys.exit(0)

    sys.stderr.write(data)


if __name__ == '__main__':
    main()
