#!/bin/bash

# Script to translate 100000 entries in pb.txt from English to language X
# TLR Halbesma, April 20th 2014, Version 1.0: implemented.
# sudo apt-get install dictd
# sudo apt-get install dict-freedict-eng-nld

set -o errexit

while read p; do
    english=$(echo $p | awk '{print $1}')
    #echo original $english
    raw_dutch=$(echo $english | translate-bin -s google -f en -t nl)
    dutch=$(echo $raw_dutch | cut -d ">" -f 2)
    echo $dutch
done < pb.txt
