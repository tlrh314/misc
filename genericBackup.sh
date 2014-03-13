#!/bin/bash

# Shell script to backup directories.
# Files are saved as gzip tar archives with name YYDDMMHH.tar.gz.
# For the last day an hourly backup is saved (cron job runs hourly).
# For the last week a daily backup is saved.
# For the last month a weekly backup is saved.
# For the last year a monthly backup is saved.
# Free disk space required: (24+6+4+11) * source_dir_size MB = x MB.

# TLR Halbesma, march 13, 2014. Version 2.0; changed for generic use.

set -o errexit

# Date Format
now=`date +%Y%m%d%H`

# Set to true if output should be saved to logfile, conversely set to false.
verbose=true

# PATHs
dest_dir="/path/to/backup_dir"
src="/path/to/source_dir"
src2="/path/to/second_source_dir"
logfile="/path/to/log.txt"
dest="$dest_dir/$now.tar.gz"

# Handle the user-specified parameters.

# Help function.

# Inform user if verbose=true
if [[ "$verbose" && ! -s $logfile ]]
then
    echo -e "Generic backupscript\n" >> $logfile
    date >> $logfile
    echo -e "Backing up:    $src\nto:            $dest" >> $logfile
fi

# Do the backing up
tar -zcPf $dest $src $src2

# Delete old directories to save on space.

# Should file be kept (return 0=true) or deleted (return 1=false).
# Usage: "keep YYYYMMDDHH.tar.gz"; function called with filename (= $1).
keep() {
    # Time right now in UNIX time.
    now=`date --date now +%s`

    # Filename is YYYYMMDDHH.tar.gz where Y=year M=month D=day H=hour.
    year=`echo $1 | cut -c 1-4`
    month=`echo $1 | cut -c 5-6`
    day=`echo $1 | cut -c 7-8`
    hour=`echo $1 | cut -c 9-10`

    # Timestamp is the UNIX time in seconds.
    timestamp="$(date --utc --date "$year-$month-$day $hour:00 CEST" +%s)"

    # Convert month, day and hour to base 10. 0x is interpreted as base 8.
    month=$((10#$month))
    day=$((10#$day))
    hour=$((10#$hour))

    # Time difference in seconds from creation time untill now.
    diff=`expr $now - $timestamp`

    if (($diff < 24*3600))
    then
        # Younger than 24h.
        return 0
    elif (($diff < 7*24*3600)) && (($hour == "00"))
    then
        # Younger than a week. Keep daily copy (made at midnight).
        return 0
    elif (($diff < 31*24*3600)) && ((`expr $day % 7` == 1)) && (($hour == "00"))
    then
        # Introducing a little error with the '31'.
        # Younger than a month. Keep weekly copy (made n*7+1th day at midnight)
        return 0
    elif (($diff < 365*24*3600)) && (($day == "01")) && (($hour == "00"))
    then
        # Younger than a year. Keep monthly copy (made first day at midnight)
        return 0
    fi

    # Default is to delete the file.
    return 1
}

for file in $dest_dir/*;
do
    # Strip filename from path when calling keep()
    if ! keep ${file##*/};
    then
        if [[ "$verbose" && -f $logfile ]]
        then
            echo "Deleting $file\n" >> $logfile
        fi
        rm -f $file
    fi
done
