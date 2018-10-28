#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from argparse import ArgumentParser
from imaplib import IMAP4_SSL
from email import message_from_string
from email.policy import SMTPUTF8

from sys import exit

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
                    # found = found[1:5]
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
                log.info('Logout user: "{u}"'.format(u=options.username))
                # Logout before continuing
                imap.logout()
    # Success
    return messages


def main():
    """Main entry point
    :returns: TODO

    Statistics:
    - List of unique e-mail addresses
    - Nr. of e-mails per month
    - Nr. E-mails with attachments
    """
    options = parse()
    try:
        # Setup logging
        logger(options)

        # Retrieve all messages from the server
        messages = get_messages(options)
        log.info('{s:-^80}'.format(s=' E-mail Messages '))
        for msg in messages:
            try:
                # log.debug(msg.keys())
                log.info('{d} | {f: <40.40} | {s: <40.40}'.format(
                         f=msg['From'], s=msg['Subject'], d=msg['Date']))
            except TypeError:
                continue

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
