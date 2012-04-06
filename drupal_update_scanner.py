#!/usr/bin/env python
import sys
import os
import subprocess
import smtplib
from email.mime.text import MIMEText
import argparse

parser = argparse.ArgumentParser(description='Scan for Drupal updates.')
parser.add_argument("-d", "--dir", dest="scandir", required=True,
                  help="which directory contains your drupal directories?", metavar="SCAN_DIRECTORY")
parser.add_argument("-f", "--file", dest="filename",
                  help="write report to specific FILE", metavar="FILE")
parser.add_argument("-m", "--mail", dest="mailaddresses",
                  help="send report to email address or addresses \
                  e.g., --mail \"foo@foo.com,bar@bar.com\"", metavar="ADDRESSES")
parser.add_argument("-s", "--subject", dest="mailsubject", default="UPDATE REPORT",
                  help="set email subject e.g., --subject=\"Update Alert!\"",
                  metavar="\"SUBJECT\"")
parser.add_argument("-q", "--quiet",
                  action="store_false", dest="verbose", default=True,
                  help="do not show output")
args = parser.parse_args()

# Execute a bash command and return the stdout
def runBash(cmd):
    p = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE)
    out = p.stdout.read().strip()
    return out

TEMPFILE = '/tmp/allupdates.txt'

# Clean up the paths to fix any problems we might
# have with user paths (--dir=~/xyz won't work otherwise)
args.scandir = os.path.expanduser(args.scandir)
if args.filename:
    args.filename = os.path.expanduser(args.filename)

# We need to write to a temp file if -m OR -f are used!
if args.mailaddresses or args.filename:
    if os.path.exists(TEMPFILE): 
        os.remove(TEMPFILE)
    f = open(TEMPFILE, 'w')

if args.filename:
    if os.path.exists(args.filename):
        sys.exit("The file specified already exists!")

# Store the directory from which the user is executing this script
# so we can store a file (if they use -f/--file) relative to this directory
origdir = os.getcwd()

# Move to the directory that contains the Drupal sites
os.chdir(args.scandir)

root, dirs, files = os.walk('.').next()

for name in dirs:
    os.chdir(name)
    if os.path.exists('modules'):
        if args.verbose:
            print name
        results = runBash('drush pm-update --simulate | grep "UPDATE\|not supported"')
        if results:
            if args.verbose:
                print results
            if args.mailaddresses or args.filename:
                f.write("###################################\n")
                f.write(name + "\n " + results.replace("\r\n", "\n") + "\n\n")
        else:
            if args.verbose:
                print "No updates found"
    os.chdir(args.scandir)

if args.mailaddresses or args.filename:
    f.close()

# Move back to where the user started
os.chdir(origdir)

if args.mailaddresses:
    print "Sending email to %s" % args.mailaddresses

    f = open(TEMPFILE, 'rb')
    msg = MIMEText(f.read(), 'plain')
    f.close()

    msg['Subject'] = args.mailsubject
    msg['From'] = 'adam@transitid.com'
    msg['To'] = args.mailaddresses

    # This requires that a local SMTP server is running (e.g., postfix)
    s = smtplib.SMTP('localhost')
    s.sendmail('adam@transitid.com', [args.mailaddresses], msg.as_string())
    s.quit()

if args.filename:
    os.system("mv %s %s" % (TEMPFILE, args.filename))

# Just in case the user doesn't want this hanging around
if os.path.exists(TEMPFILE): 
    os.remove(TEMPFILE)
