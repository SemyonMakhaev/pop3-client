"""A tool for POP3-server reply parsing."""
import re

from threading import Thread
from os import linesep
from base64 import b64decode
from quopri import decodestring
from logging import warning


CRLF = "\r\n"
FROM = re.compile(r"From: (.*){}".format(CRLF))
TO = re.compile(r"To: (.*){}".format(CRLF))
DATE = re.compile(r"Date: (.*){}".format(CRLF))
BOUNDARY = re.compile(r'boundary="(.*?)"')
SUBJECT = re.compile(r"Subject: (.*){}".format(CRLF))
SIZE = re.compile(r"\+OK (\d+) octets")
NAME = re.compile(r'name="(.*)"')
CODING = re.compile(r"=\?(.*?)\?(.)\?(.*?)\?=")


class Letter(Thread):
    """A letter representation."""
    def __init__(self, data, number):
        super(Letter, self).__init__()
        self._data = data.decode()
        self.number = number
        self.from_field = "?"
        self.to_field = "?"
        self.date = "?"
        self.size = "?"
        self.subject = "?"
        self.attachments = []


    def run(self):
        """A letter parsing."""
        from_field = self.decode(FROM)
        subject = self.decode(SUBJECT)
        self.from_field = decode_field(from_field)
        self.subject = decode_field(subject)

        self.to_field = self.decode(TO)
        self.date = self.decode(DATE)
        self.size = self.decode(SIZE)

        for line in self._data.split(CRLF):
            match = re.search(NAME, line)
            if match is not None:
                name = match.groups()[0]
                self.attachments.append(name)


    def __repr__(self):
        number = "Number: {}{}".format(self.number, linesep)
        from_field = "From: {}{}".format(self.from_field, linesep)
        to_field = "To: {}{}".format(self.to_field, linesep)
        date = "Date: {}{}".format(self.date, linesep)
        size = "Size: {}{}".format(self.size, linesep)
        subject = "Subject: {}{}".format(self.subject, linesep)
        result = number + from_field + to_field + subject + date + size

        if len(self.attachments) == 0:
            result += "No attachment{}".format(linesep)

        else:
            result += "Attachments count: {0}{1}Attachments:{1}".format(\
                                        len(self.attachments), linesep)

            for attachment in self.attachments:
                result += "\t{}{}".format(attachment, linesep)

        return result


    def decode(self, pattern):
        """Return a result of matching."""
        try:
            return re.search(pattern, self._data).groups()[0]

        except AttributeError:
            warning("Decoding error in letter %s", self.number)
            return "?"


def decode_field(line):
    """Decoding of from and subject fields."""
    match = re.search(CODING, line)

    if match is None:
        return line

    coding, transport_coding, data = match.groups()

    if transport_coding == "B":
        return b64decode(data).decode(coding)

    if transport_coding == "Q":
        return decodestring(data).decode(coding)
