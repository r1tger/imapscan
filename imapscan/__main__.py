#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import pandas as pd

from argparse import ArgumentParser
from imaplib import IMAP4_SSL
from email import message_from_string
from email.policy import SMTPUTF8

from sys import exit
from re import search

import logging
log = logging.getLogger(__name__)

LOG_FORMAT = '[%(asctime)s] [%(levelname)s] %(message)s'


def logger(options):
    """ """
    # Set up logging
    if options.log:
        handler = logging.FileHandler(options.log)
    else:
        handler = logging.StreamHandler()
    handler.setFormatter(logging.Formatter(LOG_FORMAT))
    # Add handler to the root log
    logging.root.addHandler(handler)
    # Set log level
    level = logging.DEBUG if options.debug else logging.INFO
    logging.root.setLevel(level)


def parse():
    """TODO: Docstring for parse.
    :returns: TODO
    """
    parser = ArgumentParser()
    # Shared
    parser.add_argument('--debug', help='enable debug mode',
                        action="store_true", default=False)
    parser.add_argument('--log', help='log file')
    parser.add_argument('--host', required=True, help='RPC hostname')
    parser.add_argument('--username', required=True, help='IMAP username')
    parser.add_argument('--password', default='', help='IMAP password')
    parser.add_argument('--mailbox', action='append', required=True,
                        help='IMAP mailboxes to process')
    parser.add_argument('--find', default='', required=True,
                        help='search criteria to match e-mails against')
    parser.add_argument('--limit', help='max number of messages to retrieve',
                        type=int)
    file_operations = parser.add_mutually_exclusive_group()
    file_operations.add_argument('--in-file', help='input DataFrame (CSV)')
    file_operations.add_argument('--out-file', help='output DataFrame (CSV)')
    # Parse options
    return parser.parse_args()


def get_message(imap, num):
    """ """
    try:
        # Download the message
        _, data = imap.fetch(num, '(RFC822)')
        # Parse e-mail message
        return message_from_string(data[0][1].decode(), policy=SMTPUTF8)
    except TypeError:
        # Catch any parse errors, keep going
        return None


def get_messages(options):
    """ """
    done = False
    retrieved = {}
    messages = []

    # Keep processing until all messages are retrieved
    while not done:
        with IMAP4_SSL(host=options.host) as imap:
            # Login
            log.info('Login user: "{u}"'.format(u=options.username))
            imap.login(user=options.username, password=options.password)
            try:
                # Process each mailbox
                for mailbox in options.mailbox:
                    # Keep track of retrieved files
                    if mailbox not in retrieved:
                        retrieved[mailbox] = []
                    # Select the INBOX and disallow modifications
                    imap.select(mailbox=mailbox, readonly=True)
                    log.info('Processing mailbox "{m}"'.format(m=mailbox))
                    # Search for messages by search parameter
                    _, data = imap.search(None, '(TO {s})'.format(
                                          s=options.find))
                    # Remove retrieved messages from list
                    found = data[0].split()
                    if options.limit:
                        found = found[1:options.limit]
                    found = [x for x in found if x not in retrieved[mailbox]]
                    log.info('Processing {n} messages'.format(n=len(found)))
                    # Get message
                    for num in found:
                        # Fetch the email message from the server
                        msg = get_message(imap, num)
                        if msg is not None:
                            messages.append(msg)
                        retrieved[mailbox].append(num)
                # We're done, stop processing
                done = True
            except imap.abort:
                # Drop out of processing and reconnect
                log.info('Lost connection, reconnecting')
                continue
            else:
                # Logout before continuing
                log.info('Logout user: "{u}"'.format(u=options.username))
                imap.logout()
    # Success
    return messages


def get_rows(messages):
    """ """
    rows = []
    for msg in messages:
        try:
            # Create a new row based on the EmailMessage
            date = pd.to_datetime(msg['Date'])
            row = {'From': msg['From'], 'To': msg['To'],
                   'Subject': msg['Subject'],
                   'Date': date,
                   'Month': date.to_period('M'),
                   'X-Spam-Flag': msg['X-Spam-Flag'],
                   'Message-ID': msg['Message-ID'],
                   'Has-Attachment': 'Yes' if has_attachment(msg) else 'No'}
            rows.append(row)
            # log.debug(msg.keys())
            # log.info('{d} | {f: <40.40} | {s: <40.40}'.format(
            #          f=msg['From'], s=msg['Subject'], d=msg['Date']))
        except TypeError:
            continue
    return rows


def get_unique_addresses(df):
    """ """
    addresses = []
    for _, row in df.iterrows():
        addresses += get_unique_address(row['From'])
        addresses += get_unique_address(row['To'])
    return set(addresses)


def get_unique_address(row):
    """ """
    addresses = []
    for ea in row.split(', '):
        m = search(r'<(.+)>', ea)
        address = m.group(1) if m is not None else ea.strip()
        if '@' in address:
            # Quick sanity check
            addresses.append(address)
    return addresses


def has_attachment(msg):
    """ Process each multipart of a message and check if an attachment is
    found """
    for part in msg.walk():
        if part.is_attachment():
            return True
    return False


def format_series(series):
    """ """
    values = []
    for index, value in series.items():
        values.append('({i}, {v})'.format(i=index, v=value))
    return ' '.join(values)


def main():
    """ Main entry point """
    options = parse()
    try:
        # Setup logging
        logger(options)

        if options.in_file:
            # Load CSV provided on command line
            df = pd.read_csv(options.in_file, encoding='utf-8')
        else:
            # Retrieve all messages from the server
            messages = get_messages(options)
            log.info('{s:-^80}'.format(s=' E-mail Messages '))
            # Retrieve all rows for the messages
            rows = get_rows(messages)

            # Create a new DataFrame from the rows
            df = pd.DataFrame(rows)
            if options.out_file:
                df.to_csv(options.out_file, encoding='utf-8', index=False)

        log.info('{s:-^80}'.format(s=' Statistics '))

        # Number of e-mails
        log.info('Total number of e-mails: {c}'.format(c=len(df)))
        # List of unique e-mail addresses
        addresses = get_unique_addresses(df)
        log.info('Unique e-mail addresses: {e}'.format(e=len(addresses)))
        log.debug(addresses)

        log.info('{s:-^80}'.format(s=' Table Data '))

        # Number of e-mails per month
        log.info(format_series(df.groupby('Month').size()))
        # Number of e-mails that have an attachment
        log.info(format_series(df.groupby('Has-Attachment').size()))

        # Success
        return(0)
    except KeyboardInterrupt:
        log.info('Received <ctrl-c>, stopping')
    except Exception as e:
        log.exception(e) if options.debug else log.error(e)
    finally:
        # Return 1 on any caught exception
        return(1)


if __name__ == "__main__":
    exit(main())
