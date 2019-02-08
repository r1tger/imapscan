# imapscan

# Installing
To get up and running, install directly from Github into a python virtualenv:
```bash
$ python3 -m venv imapscan
$ source imapscan/bin/activate
$ pip install git+https://github.com/r1tger/imapscan
$ imapscan --help
```

# Using
```bash
$ imapscan --help
usage: imapscan [-h] [--debug] [--log LOG] --host HOST --username USERNAME
                [--password PASSWORD] --mailbox MAILBOX --find FIND
                [--limit LIMIT] [--attachments ATTACHMENTS]
                [--in-file IN_FILE | --out-file OUT_FILE]

optional arguments:
  -h, --help            show this help message and exit
  --debug               enable debug mode
  --log LOG             log file
  --host HOST           RPC hostname
  --username USERNAME   IMAP username
  --password PASSWORD   IMAP password
  --mailbox MAILBOX     IMAP mailboxes to process
  --find FIND           search criteria to match e-mails against
  --limit LIMIT         max number of messages to retrieve
  --attachments ATTACHMENTS
                        Output directory for attachments
  --in-file IN_FILE     input DataFrame (CSV)
  --out-file OUT_FILE   output DataFrame (CSV)
```

# Developing
If you'd like to contribute to development of imapscan, set up a development
environment:
```bash
$ git clone https://github.com/r1tger/imapscan
$ cd imapscan
$ python3 -m venv env
$ source env/bin/activate
$ pip install --editable .
```
Now edit any files in the ```imapscan/``` package and submit a pull request.

# TO-DO
* Add documentation
* Add test cases
