misc: Random bits and pieces of coding.
====


**KillStartupChime.sh**

OSX has this annoying startup sound that tends to mess with me whenever I'm studying some place quiet. Run this script once, then press 1 to create mute on and off scripts. Those scripts are then set as login and logout hooks. This script uses OS X's behavior to remember the last volume before shutdown as the startup volume. Mute before shutdown and the annoying startup chime has been killed! To undo simply run the script using option 2.

**autoUpdate.sh**

Script to run in a daily cronjob at night to update and upgrade my packes. Furthermore, I have noticed that even after a single day my clock has a significant offset, thus, the nightly autoUpdate script syncs the time too.

**genericBackup.sh**

Some directories should be backupped periodically. This script runs in an hourly cronjob to make this happen.

**vm201.py**

Script to read status of channels in a VM201 ethernet relay card.
http://www.vellemanprojects.eu/products/view/?country=be&lang=en&id=407510
http://www.velleman.eu/downloads/0/infosheets/datasheet_vm201-uk.pdf
http://forum.velleman.eu/viewtopic.php?f=37&t=8598&p=33039&hilit=VM201+protocol
