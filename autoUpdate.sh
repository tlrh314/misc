#!/bin/bash
# Script to automatically update, upgrade and autoclean. Run daily at night.
# TLR Halbesma, January 11, 2014. Version 2.2: clear logfile; add apt-check;
# update date
set -o errexit

logfile="/var/log/auto_update.log"

if [ -f $logfile ]; then
    rm $logfile
    touch $logfile
fi

# Update blody time while we're at it. There's usually a significant offset.
/usr/sbin/ntpdate ntp.ubuntu.com >> $logfile

date >> $logfile
/usr/lib/update-notifier/apt-check --human-readable >> $logfile

(/usr/bin/apt-get update && /usr/bin/apt-get upgrade -y && \
    /usr/bin/apt-get autoclean && /usr/bin/apt-get check) 2>&1 >> $logfile
echo -e "\nSuccess!\n" >> $logfile

date >> $logfile
/usr/lib/update-notifier/apt-check --human-readable >> $logfile
