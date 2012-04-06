#!/usr/bin/env python
import sys
import os
import subprocess
import smtplib
from email.mime.text import MIMEText
from optparse import OptionParser

parser = OptionParser()
parser.add_option("-f", "--file", dest="filename",
                  help="write report to specific FILE", metavar="FILE")
parser.add_option("-m", "--mail", dest="mailaddresses",
                  help="send report to email address or addresses \
                  e.g., --mail \"foo@foo.com,bar@bar.com\"", metavar="ADDRESSES")
parser.add_option("-s", "--subject", dest="mailsubject", default="UPDATE REPORT",
                  help="set email subject e.g., --subject=\"Update Alert!\"",
                  metavar="\"SUBJECT\"")
parser.add_option("-q", "--quiet",
                  action="store_false", dest="verbose", default=True,
                  help="do not show output")
(options, args) = parser.parse_args()

# Execute a bash command and return the stdout
def runBash(cmd):
    p = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE)
    out = p.stdout.read().strip()
    return out

# We need to write to a temp file if -m OR -f are used!
if options.mailaddresses or options.filename:
    TEMPFILE = '/tmp/allupdates.txt'
    if os.path.exists(TEMPFILE): 
        os.remove(TEMPFILE)
    f = open(TEMPFILE, 'w')

if options.filename:
    if os.path.exists(options.filename): 
        sys.exit("The file specified already exists!")
root, dirs, files = os.walk('.').next()
workingdir = os.getcwd()

for name in dirs:
    os.chdir(name)
    if os.path.exists('modules'):
        if options.verbose:
            print name
        results = runBash('drush pm-update --simulate | grep "UPDATE\|not supported"')
        if results:
            if options.verbose:
                print results
            if options.mailaddresses or options.filename:
                f.write("###################################\n")
                f.write(name + "\n " + results.replace("\r\n", "\n") + "\n\n")
        else:
            if options.verbose:
                print "No updates found"
    os.chdir(workingdir)

f.close()

if options.mailaddresses:
    print "Sending email to %s" % options.mailaddresses

    f = open(TEMPFILE, 'rb')
    msg = MIMEText(f.read())
    f.close()

    msg['Subject'] = options.mailsubject
    msg['From'] = 'adam@transitid.com'
    msg['To'] = options.mailaddresses

    # This requires that a local SMTP server is running (e.g., postfix)
    s = smtplib.SMTP('localhost')
    s.sendmail('adam@transitid.com', [options.mailaddresses], msg.as_string())
    s.quit()

if options.filename:
    os.system("mv %s %s" % (TEMPFILE, options.filename))

# Just in case the user doesn't want this hanging around
if os.path.exists(TEMPFILE): 
    os.remove(TEMPFILE)
