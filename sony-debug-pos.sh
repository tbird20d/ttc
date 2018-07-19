#!/bin/sh
#
# sony-debug-pos.sh - report the power-on-status (POS) for a Sony debug board.
#
# For some reason, I don't always get a valid response from the board.
# Use sampling and report the most-often-reported answer.

usage() {
    cat <<HERE
Usage: sony-debug-pos.sh <ctrl-tty>"

<ctrl-tty> is the tty serial device in Linux where the Sony"
debug board reports its status. e.g. /dev/ttyACM0"
HERE
    exit 1
}

ctrl_dev=$1
if [ -z $ctrl_dev ]; then
    echo "Error: Missing ctrl-tty"
    usage
fi

if [ "$ctrl_dev" = "-h" ]; then
    usage
fi

# read 20 lines from ctrl-dev, grep for 'VBus', take the last line
# and parse the word following "VBus:"
# This should be either ON or OFF
cat $ctrl_dev 2>/dev/null | head -n 20 | grep -a VBus | tail -n 1 | \
    sed "s/.*VBus:\([a-zA-Z]*\).*/\1/"
exit 0
