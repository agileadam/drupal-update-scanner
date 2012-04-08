#!/usr/bin/env python
import sys
import os
import subprocess
import smtplib
from email.mime.text import MIMEText
import argparse
import glob

parser = argparse.ArgumentParser(description='Scan for Drupal updates.')
parser.add_argument("-d", "--dir", dest="scandir", required=True,
                  help="which directory contains your drupal sites (you can optionally \
                  traverse deeper from this root directory using the -t/--traverse argument)",
                  metavar="SCAN_DIRECTORY")
parser.add_argument("-o", "--output-file", dest="outputfile",
                  help="write report to specific FILE", metavar="FILE")
parser.add_argument("-t", "--traverse", dest="traverse", default=0, type=int,
                  help="how many levels deep to scan for drupal sites", metavar="N")
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

# Exit as early as possible; if output file
# already exists, exit with message
if args.outputfile:
    if os.path.exists(args.outputfile):
        sys.exit("The file specified already exists!")

# Execute a bash command and return the stdout
def runBash(cmd):
    p = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE)
    out = p.stdout.read().strip()
    return out

# Process a Drupal directory (dir MUST be a Drupal directory
# as we're not checking this here!)
def processDir(dir):
    os.chdir(dir)
    if args.verbose:
        print dir
    drush = subprocess.Popen(['drush', 'pm-update', '--simulate'],
                             stdout=subprocess.PIPE,
                             )
    grep = subprocess.Popen(['grep', '"UPDATE\|not supported"'],
                             stdin=drush.stdout,
                             stdout=subprocess.PIPE,
                             )
    results = grep.stdout.read()
    if results:
        if args.verbose:
            print results
        if args.mailaddresses or args.outputfile:
            f.write("###################################\n")
            f.write(dir + "\n " + results.replace("\r\n", "\n") + "\n\n")
    else:
        if args.verbose:
            print "No updates found"
    os.chdir(args.scandir)

TEMPFILE = '/tmp/allupdates.txt'

# Clean up the paths to fix any problems we might
# have with user paths (--dir=~/xyz won't work otherwise)
args.scandir = os.path.expanduser(args.scandir)
if args.outputfile:
    args.outputfile = os.path.expanduser(args.outputfile)

# We need to write to a temp file if -m OR -f are used!
if args.mailaddresses or args.outputfile:
    if os.path.exists(TEMPFILE): 
        os.remove(TEMPFILE)
    f = open(TEMPFILE, 'w')

# Store the directory from which the user is executing this script
# so we can store a file (if they use -f/--file) relative to this directory
origdir = os.getcwd()

# Move to the directory that contains the Drupal sites
os.chdir(args.scandir)

root, dirs, files = os.walk('.').next()

# Traverse into subdirectories until the --traverse depth is reached
count = 0
while (count <= args.traverse):
    count = count + 1
    wildcards = '*/' * count
    for name in glob.glob(wildcards + 'sites/all/modules'):
        processDir(name.replace('/sites/all/modules', ''))

if args.mailaddresses or args.outputfile:
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

if args.outputfile:
    os.system("mv %s %s" % (TEMPFILE, args.outputfile))

# Just in case the user doesn't want this hanging around
if os.path.exists(TEMPFILE): 
    os.remove(TEMPFILE)
