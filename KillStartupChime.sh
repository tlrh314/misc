#! /bin/bash
#kill the annoying startup chime' by Timo Halbesma, March 27 2012
# timohalbesma@gmail.com

ON_FILE="~/Desktop/mute-on.sh"
OFF_FILE="~/Desktop/mute-off.sh"
NOW=$(date +"%B %d, %Y")

function remove() {
    if [ -e $ON_FILE ]; then
        sudo rm -f $ON_FILE
    fi

    if [ -e $OFF_FILE ]; then
        sudo rm -f $OFF_FILE
    fi
}

function doinstall() {
    # Remove currect script if one exists
    remove
    # Create the ON and OFF scripts

    sudo sh -c "echo \"#! /bin/bash
# Kill the annoying tartup chime by Timo Halbesma, $NOW
# timohalbesma@gmail.com
    osascript -e 'set volume with output muted'\" >> $ON_FILE"

        sudo sh -c "echo \"#! /bin/bash
# Kill the annoying tartup chime by Timo Halbesma, $NOW
# timohalbesma@gmail.com
    osascript -e 'set volume without output muted'\" >> $OFF_FILE"

    # Chmod the ON and OFF scripts to +x to make then executable.
    if [-e $ON_FILE ]; then
        sudo chmod +x $ON_FILE
        sudo chmod +x $OFF_FILE
    else
        echo "Something went wrong!"
    fi

    # Write the LoginHook and the LoginHook
    sudo defaults write com.apple.loginwindow LogoutHook $ON_FILE
    sudo defaults write com.apple.loginwindow LoginHook $OFF_FILE

    # Notify user
    #osascript -e 'set volume 10'
    #echo "The annoying startup sound has been removed"
    #say The annoying startup sound has been removed

    exit
}

function uninstall() {
    # Remove currect script if one exists
    remove

    # Delete the LoginHook and the LoginHook
    sudo defaults delete com.apple.loginwindow LogoutHook
    sudo defaults delete com.apple.loginwindow LoginHook

    exit
}

while :
do
    clear
    echo -e "Kill the startup chime by Timo Halbesma\n"
    echo -e "[1]Install\n[2]Uninstall\n[3]Quit"
    echo -n "1/2/3: "
    read opt
    case $opt in
        1) doinstall;;
        2) uninstall;;
        3) echo "bye $USER"; exit;;
        *) echo "$opt is an invalid option. Please enter '1' or '2' or '3'";
        echo "Press [enter] to continue"
        read enterKey;;
    esac
done
