This is a python script that scans a server for sites that need Drupal updates, and outputs a report (to screen or file) that shows which updates are required for each site. A popular implementation is to run this via a cronjob and pipe the command to a mail application to email the output.

*The first time you run the script you should run it with the -h or --help option.*

# Requirements

* Drush
* Python (at least version 2.7)

# Cronjobs
One of the main reasons to use a script like this is to have automatic, daily update checks for all sites on a server. It's very convenient to get a single email every morning from your server showing which sites need which updates.

*If you're running the script from a cronjob, make sure that Drush is somewhere in the cron user's $PATH.*

Here's an example cronjob (all on a single line):

* It runs every day at 02:15
* The output is emailed to agileadam@gmail.com
* The Drupal sites are located up to one level below /webapps/
(e.g., _/webapps/*/httpdocs_)

<code>15  2   *   *   *   /usr/local/bin/python2.7 /usr/local/bin/drupal_update_scanner.py</code>
<code>-d /webapps/ -t 1 | mail -s "Drupal updates for server123" agileadam@gmail.com</code>
