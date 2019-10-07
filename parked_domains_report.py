#!/usr/bin/env python

import subprocess
import csv
import datetime
import os
import configparser

# Import configuration file with secrets
config = configparser.ConfigParser()
config.read('config.ini')

# Import password from config file
user = config['cpanel-info']['user']
password = config['cpanel-info']['password']

# Move last report to have .old extension
if os.path.exists("output/report-parked-domains.csv"):
    os.rename("output/report-parked-domains.csv", "output/report-parked-domains.csv.old")

# Get /etc/userdomains from each cpanel server and combine into one file
subprocess.call("wget -q ftp://%s:%s@cpanel-6/userdomains -O tmp/parked_domains6" % (user,password), shell = True)
subprocess.call("wget -q ftp://%s:%s@cpanel-7/userdomains -O tmp/parked_domains7" % (user,password), shell = True)
subprocess.call("wget -q ftp://%s:%s@cpanel-8/userdomains -O tmp/parked_domains8" % (user,password), shell = True)

# Join all files to one file
subprocess.call("cat tmp/parked_domains6 tmp/parked_domains7 tmp/parked_domains8 > tmp/userdomains", shell = True, stdout=subprocess.PIPE)

# Open file into memory and strip news lines
userdomains = subprocess.Popen("cat /home/jonathanweaver/reports/parked_domains/tmp/userdomains", shell=True, stdout=subprocess.PIPE).communicate()[0].strip()
userdomains = userdomains.decode().split("\n")

# Flip words so that account is in front of parked domain for sorting
for line in userdomains:
    entries = line.split(": ")
    subprocess.call("echo %s, %s>> tmp/userdomains.arranged" % (entries[1], entries[0]), shell = True)

# Sort the file by account name
subprocess.call("sort tmp/userdomains.arranged > tmp/userdomains.sorted", shell = True)

# Open sorted file into memory
#userdomains_sorted = subprocess.Popen("cat /home/jonathanweaver/reports/parked_domains/tmp/userdomains.sorted", shell=True, stdout=subprocess.PIPE).communicate()[0].strip()

# Initialize CSV module to write output file
with open('output/report-parked-domains.csv','w') as csv_file: # May need to change 'w' to 'wb' in Python2
    writer = csv.writer(csv_file, delimiter=",", quotechar='"')
    infile = open('tmp/userdomains.sorted').readlines()
    for line in infile:
        entries = line.split(", ")
        parked_domains = entries[1].strip("\n")
        account_entries = entries[0].upper()
        writer.writerow([account_entries, parked_domains])

# Recipients should be included in comma delimited list, inside of one set of quotes e.g. "a@intinc.com, b@intinc.com, c@intinc.com"
filenm = "output/report-parked-domains.csv"
emailto = "jhw@intinc.com"
todaysdate = datetime.date.today()

subprocess.Popen("/bin/mailx -a %s -s 'cPanel Parked Domains Report for %s' %s < messagebody.txt" % (filenm, todaysdate, emailto), shell = True)

# File cleanup
os.remove("tmp/parked_domains6")
os.remove("tmp/parked_domains7")
os.remove("tmp/parked_domains8")

os.remove("tmp/userdomains")
os.remove("tmp/userdomains.arranged")
os.remove("tmp/userdomains.sorted")
