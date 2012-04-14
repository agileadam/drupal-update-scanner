#!/usr/bin/env python
#
# Cronjob example (single line):
# /usr/local/bin/python2.7 /usr/local/bin/drupal_update_scanner.py -d /webapps/
#      -t 1 | mail -s "Drupal updates for Server X" agileadam@gmail.com

import sys
import os
import subprocess
import argparse
import glob

parser = argparse.ArgumentParser(description='Scans a server for sites that need Drupal updates, and outputs a report (to screen or file) that shows which updates are required for each site. A popular implemntation is to run this via a cronjob and pipe the command to a mail application to email the output. View the source code for more help!')
parser.add_argument("-d", "--dir", dest="scandir", required=True,
                  help="which directory contains your drupal sites (you can optionally \
                  traverse deeper from this root directory using the -t/--traverse argument)",
                  metavar="SCAN_DIRECTORY")
parser.add_argument("-a", "--report-all", default=False, dest="reportall",
                  action="store_true", help="include all Drupal sites in the output, \
                  regardless of update status")
parser.add_argument("-o", "--output-file", dest="outputfile",
                  help="write report to specific FILE", metavar="FILE")
parser.add_argument("-t", "--traverse", dest="traverse", default=0, type=int,
                  help="how many levels deep to scan for drupal sites", metavar="N")
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

# Emulate the which binary
# http://stackoverflow.com/a/377028
def which(program):
    def is_exe(fpath):
        return os.path.isfile(fpath) and os.access(fpath, os.X_OK)

    fpath, fname = os.path.split(program)
    if fpath:
        if is_exe(program):
            return program
    else:
        for path in os.environ["PATH"].split(os.pathsep):
            exe_file = os.path.join(path, program)
            if is_exe(exe_file):
                return exe_file

    return None

# Look for Drush and store its location; quit if we cannot find it
drush_app = which('drush')
if drush_app == None:
    sys.exit("Couldn't not find the Drush application in $PATH. If you are \
running this from a cronjob, try setting cron's PATH to include the drush \
application.")

# Process a Drupal directory (dir MUST be a Drupal directory
# as we're not checking this here!)
def processDir(dir):
    os.chdir(dir)
    drush = subprocess.Popen([drush_app, 'pm-update', '--pipe', '--simulate',
                             '--security-only'],
                             stdout=subprocess.PIPE,
                             )
    results = drush.stdout.read()
    if results:
        if args.verbose:
            print "###################################\n" + dir
            print results
        if args.outputfile:
            f.write("###################################\n")
            f.write(dir + "\n " + results.replace("\r\n", "\n"))
    else:
        if args.verbose and args.reportall:
            print "###################################\n" + dir
            print "No updates found\n\n"
    os.chdir(args.scandir)

TEMPFILE = '/tmp/allupdates.txt'

# Clean up the paths to fix any problems we might
# have with user paths (--dir=~/xyz won't work otherwise)
args.scandir = os.path.expanduser(args.scandir)
if args.outputfile:
    args.outputfile = os.path.expanduser(args.outputfile)

# We need to write to a temp file if -m OR -f are used!
if args.outputfile:
    if os.path.exists(TEMPFILE):
        os.remove(TEMPFILE)
    f = open(TEMPFILE, 'w')

# Store the directory from which the user is executing this script
# so we can store a file (if they use -f/--file) relative to this directory
origdir = os.getcwd()

# Move to the directory that contains the Drupal sites
os.chdir(args.scandir)

# Traverse into subdirectories until the --traverse depth is reached
count = 0
while (count <= args.traverse):
    count = count + 1
    wildcards = '*/' * count
    for name in glob.glob(wildcards + 'sites/all/modules'):
        processDir(name.replace('/sites/all/modules', ''))

if args.outputfile:
    f.close()

# Move back to where the user started
os.chdir(origdir)

# Create the final file (move it from its temporary directory)
if args.outputfile:
    os.system("mv %s %s" % (TEMPFILE, args.outputfile))

# Just in case the user doesn't want this hanging around
if os.path.exists(TEMPFILE):
    os.remove(TEMPFILE)
