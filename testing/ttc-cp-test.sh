#!/bin/sh
#
# ttc-cp-test.sh
#
# run a number of tests of the 'ttc cp' command
#
# To do:
# - additional tests
#   - bad syntax - mispelled target:  ttc cp $SRC_DIR/ targt:$BOARD_DIR
#   - bad syntax - missing target: ttc cp foo bar
#   - bad input - missing src file: ttc cp not-here target:$BOARD_DIR
#   - bad input - missing dest dir: ttc cp $SEND_DIR/foo target:/not-there
#   - wildcards - ex: ttc cp $SEND_DIR/sub* target:$BOARD_DIR
#   - mixed files and dir: ttc cp $SEND_DIR/foo $SEND_DIR/subdir2 target:$BOARD_DIR
#   - file already existing - ttc cp $SEND_DIR/foo target:$BOARD_DIR ;
#        ttc cp $SEND_DIR/foo target:$BOARD_DIR
#   - dir already existing - ttc cp $SEND_DIR/subdir target:$BOARD_DIR ;
#        ttc cp $SEND_DIR/subdir target:$BOARD_DIR
#   - should try some file encodings that would be problematic for some transports
#

# uncomment this to debug the script
#set -x

# this is the default, if no board is specified
BOARD="bbb"

error_out() {
    echo "Error: $@"
    exit 1
}

v_echo() {
    if [ -n "$VERBOSE" ] ; then
        echo $@
    fi
}

##########################################################
# Parse arguments

if [ "$1" = "-h" -o "$1" = "--help" ] ; then
    cat <<HERE
Usage: ttc-cp-test.sh [-h] [-v] [<board>]

Perform a lot of file operations using 'ttc cp'

Options:
 -h, --help  Show this usage help
 -v          Show verbose output
 <board>     Perform tests on the indicated board.
             If no board is specified, use 'bbb'

Test output is in TAP format.
HERE
    exit 0
fi

export VERBOSE=
if [ "$1" = "-v" ] ; then
    export VERBOSE=1
    export TTC_V="-v"
    shift
fi

if [ -n "$1" ] ; then
    BOARD="$1"
    shift
fi

export RESULTS=/tmp/ttc-cp-results.txt

##########################################################
# Tim's shell TAP library
export TC_NUM=1

# $1 = TESTCASE name
# optional $2 = diagnostic string
# optional environment var $RESULTS, if it exists will be
#   output before the not ok line, with # prefixed on each line
#   of the file
fail() {
    if [ -f $RESULTS ] ; then
        sed "s/\(.*\)/# \1/" $RESULTS
        rm -f $RESULTS
    fi
    if [ -n "$2" ] ; then
        diag=" # $2"
    else
        diag=
    fi
    echo "not ok $TC_NUM - ${1}${diag}"
    TC_NUM="$(( $TC_NUM + 1 ))"
}

# show a TAP-formatted success line
# $1 = TESTCASE name
# optional $2 = extra diagnostic data
succeed() {
    if [ -n "$2" ] ; then
        echo "# $2"
    fi
    echo "ok $TC_NUM - $1"
    TC_NUM="$(( $TC_NUM + 1 ))"
}

setup() {
    echo "Doing temp directory setup"
    export SEND_DIR=$(mktemp -d)
    export RECV_DIR=$(mktemp -d)
    export BOARD_DIR=$(mktemp -d -u)
    ttc $TTC_V $BOARD run mkdir -p $BOARD_DIR
    v_echo "SEND_DIR='$SEND_DIR'"
    v_echo "RECV_DIR='$RECV_DIR'"
    v_echo "BOARD_DIR='$BOARD_DIR'"

    # make some test files and directories
    echo "foo" >$SEND_DIR/foo
    echo "bar" >$SEND_DIR/bar
    mkdir -p $SEND_DIR/subdir
    mkdir -p $SEND_DIR/subdir2
    mkdir -p $SEND_DIR/subdir/subsubdir1
    mkdir -p $SEND_DIR/subdir/subsubdir2
    mkdir -p $SEND_DIR/subdir2/sub2subdir1
    echo "subfoo" >$SEND_DIR/subdir/subfoo
    echo "subbar" >$SEND_DIR/subdir/subbar
    echo "subfoo1" >$SEND_DIR/subdir/subsubdir1/subfoo1
    echo "subbar1" >$SEND_DIR/subdir/subsubdir1/subbar1
    echo "subfoo2" >$SEND_DIR/subdir/subsubdir2/subfoo2
    echo "subbar2" >$SEND_DIR/subdir/subsubdir2/subbar2
    echo "subfoo2" >$SEND_DIR/subdir2/subfoo2
    echo "subbar2" >$SEND_DIR/subdir2/subbar2
    echo "subbar2" >$SEND_DIR/subdir2/sub2subdir1/subbar2

    dd if=/dev/random of=$SEND_DIR/random-data bs=1024 count=10 >/dev/null 2>&1
}

setup2() {
    dd if=/dev/random of=$SEND_DIR/big-random-data bs=1024 count=1024 >/dev/null 2>&1
}

cleanup() {
    #echo "Sleeping before cleanup - ctrl-C to stop if you need to look at stuff"
    #for i in $(seq 20) ; do echo -n "." ; sleep 1 ; done
    echo "Doing temp directory cleanup"
    rm -f $RESULTS
    rm -rf $SEND_DIR
    rm -rf $RECV_DIR
    ttc $BOARD run rm -rf $BOARD_DIR
}

# start the TAP header
echo "TAP version 13"
echo "1..12"

setup

#--------------------------------------------

desc="put a single file to a dir"
export HAVE_FILE=
ttc $TTC_V $BOARD cp $SEND_DIR/foo target:$BOARD_DIR >$RESULTS
if [ $? = "0" ] ; then
    if ttc $BOARD run "test -f $BOARD_DIR/foo" ; then
        succeed "$desc"
        HAVE_FILE=1
    else
        rm -f $RESULTS
        fail "$desc" "file not found on target"
    fi
else
    fail "$desc" "Error running ttc cp"
fi

#--------------------------------------------

desc="get a single file to a dir"
if [ -z "$HAVE_FILE" ] ; then
    # do a skip
    fail "$desc" "SKIP - missing file for test"
else
    ttc $TTC_V $BOARD cp target:$BOARD_DIR/foo $RECV_DIR >$RESULTS
    if [ $? = "0" ] ; then
       if [ -f $RECV_DIR/foo ] ; then
           if diff $SEND_DIR/foo $RECV_DIR/foo ; then
               succeed "$desc"
           else
               rm -f $RESULTS
               fail "$desc" "file does not match original"
           fi
       else
           rm -f $RESULTS
           fail "$desc" "file not found in local dir"
       fi
    else
        fail "$desc" "Error running ttc cp"
    fi
fi

#--------------------------------------------

desc="put multiple files to a dir"
FILE_COUNT=0
ttc $BOARD cp $SEND_DIR/bar $SEND_DIR/random-data target:$BOARD_DIR >$RESULTS
if [ $? = "0" ] ; then
    if ttc $BOARD run "test -f $BOARD_DIR/bar" ; then
        FILE_COUNT=1
    else
        echo "# $BOARD_DIR/bar not found on target"
    fi
    if ttc $BOARD run "test -f $BOARD_DIR/random-data" ; then
        FILE_COUNT=$(( $FILE_COUNT + 1 ))
    else
        echo "# $BOARD_DIR/random-data not found on target"
    fi
    if [ "$FILE_COUNT" = "2" ] ; then
        succeed "$desc"
    else
        rm -f $RESULTS
        fail "$desc" "one or more files not found on target"
    fi
else
    fail "$desc" "Error running ttc cp"
fi

#--------------------------------------------

desc="get multiple files to a dir"
if [ "$FILE_COUNT" != 2 ] ; then
    # do a skip
    fail "$desc" "SKIP - missing file for test"
else
    FILE_COUNT=0
    ttc $TTC_V $BOARD cp target:$BOARD_DIR/bar target:$BOARD_DIR/random-data $RECV_DIR >$RESULTS
    if [ $? = "0" ] ; then
       if [ -f $RECV_DIR/foo ] ; then
           FILE_COUNT=1
       else
           echo "# $RECV_DIR/foo not found"
       fi
       if [ -f $RECV_DIR/random-data ] ; then
           FILE_COUNT=$(( $FILE_COUNT + 1 ))
       else
           echo "# $RECV_DIR/random-data not found"
       fi
       if [ "$FILE_COUNT" = 2 ] ; then
           if diff -a $SEND_DIR/random-data $RECV_DIR/random-data ; then
               succeed "$desc"
           else
               rm -f $RESULTS
               fail "$desc" "file does not match original"
           fi
       else
           rm -f $RESULTS
           fail "$desc" "one or more files not found in local dir"
       fi
    else
        fail "$desc" "Error running ttc cp"
    fi
fi

#--------------------------------------------

desc="put single dir recursively to a dir"
export HAVE_FILE=
ttc $TTC_V $BOARD cp $SEND_DIR/subdir target:$BOARD_DIR >$RESULTS
if [ $? = "0" ] ; then
    if ttc $BOARD run "test -f $BOARD_DIR/subdir/subsubdir1/subfoo1" ; then
        succeed "$desc"
        HAVE_FILE=1
    else
        echo "# $BOARD_DIR/subdir/subsubdir1/subfoo1 not found"
        rm -f $RESULTS
        fail "$desc" "file not found on target"
    fi
else
    fail "$desc" "Error running ttc cp"
fi

#--------------------------------------------

desc="get a single dir recursively to a dir"
if [ -z "$HAVE_FILE" ] ; then
    # do a skip
    fail "$desc" "SKIP - missing data for test"
else
    ttc $TTC_V $BOARD cp target:$BOARD_DIR/subdir $RECV_DIR >$RESULTS
    if [ $? = "0" ] ; then
       if [ -f $RECV_DIR/subdir/subsubdir1/subfoo1 ] ; then
           succeed "$desc"
       else
           echo "# $RECV_DIR/subdir/subsubdir1/subfoo1 not found"
           rm -f $RESULTS
           fail "$desc" "file not found in local dir"
       fi
    else
        fail "$desc" "Error running ttc cp"
    fi
fi

#--------------------------------------------

desc="put multiple dirs recursively to a dir"
FILE_COUNT=0

# reset board directory from previous tests
ttc $BOARD run rm -rf $BOARD_DIR
ttc $TTC_V $BOARD run mkdir -p $BOARD_DIR

ttc $BOARD cp $SEND_DIR/subdir $SEND_DIR/subdir2 target:$BOARD_DIR >$RESULTS
if [ $? = "0" ] ; then
    if ttc $BOARD run "test -f $BOARD_DIR/subdir/subfoo" ; then
        FILE_COUNT=1
    else
        echo "# $BOARD_DIR/subdir/subfoo not found on target"
    fi
    if ttc $BOARD run "test -f $BOARD_DIR/subdir2/subfoo2" ; then
        FILE_COUNT=$(( $FILE_COUNT + 1 ))
    else
        echo "# $BOARD_DIR/subdir2/subfoo2 not found on target"
    fi
    if [ "$FILE_COUNT" = "2" ] ; then
        succeed "$desc"
    else
        rm -f $RESULTS
        fail "$desc" "one or more files not found on target"
    fi
else
    fail "$desc" "Error running ttc cp"
fi

#--------------------------------------------

# reset dirs from previous tests
rm -rf $RECV_DIR
mkdir -p $RECV_DIR

desc="get multiple directories recursively to a dir"
if [ "$FILE_COUNT" != 2 ] ; then
    # do a skip
    fail "$desc" "SKIP - missing file for test"
else
    FILE_COUNT=0
    ttc $TTC_V $BOARD cp target:$BOARD_DIR/subdir target:$BOARD_DIR/subdir2 $RECV_DIR >$RESULTS
    if [ $? = "0" ] ; then
       if [ -f $RECV_DIR/subdir/subfoo ] ; then
           FILE_COUNT=1
       else
           echo "# $RECV_DIR/subdir/subfoo not found"
       fi
       if [ -f $RECV_DIR/subdir2/subfoo2 ] ; then
           FILE_COUNT=$(( $FILE_COUNT + 1 ))
       else
           echo "# $RECV_DIR/subdir2/subfoo2 not found"
       fi
       if [ "$FILE_COUNT" = 2 ] ; then
           succeed "$desc"
       else
           rm -f $RESULTS
           fail "$desc" "one or more files not found in local dir"
       fi
    else
        fail "$desc" "Error running ttc cp"
    fi
fi

#--------------------------------------------

setup2

desc="put large random file (1M) to a dir"
start_time=$(date +"%s.%N")
ttc $TTC_V $BOARD cp $SEND_DIR/big-random-data target:$BOARD_DIR >$RESULTS
RCODE=$?
end_time=$(date +"%s.%N")

export HAVE_FILE=
if [ $RCODE = "0" ] ; then
    if ttc $BOARD run "test -f $BOARD_DIR/big-random-data" ; then
        succeed "$desc"
        HAVE_FILE=1
    else
        rm -f $RESULTS
        fail "$desc" "file not found on target"
    fi
else
    fail "$desc" "Error running ttc cp"
fi

#--------------------------------------------
THRESHOLD=5
desc="time to put 1M file is less than $THRESHOLD seconds"

if [ -z "$HAVE_FILE" ] ; then
    # do a skip
    fail "$desc" "SKIP - missing file for test"
else
    duration=$(python3 -c "print('%.2f' % ($end_time - $start_time))")
    dur_int=$(python3 -c "print(int($duration))")

    echo "# File copy (put) took $duration seconds"
    if [ $dur_int -lt $THRESHOLD ] ; then
        succeed "$desc"
    else
        fail "$desc"
    fi
fi

#--------------------------------------------

desc="get large random file (1M) to a dir"
if [ -z "$HAVE_FILE" ] ; then
    # do a skip
    fail "$desc" "SKIP - missing file for test"
else
    start_time=$(date +"%s.%N")
    ttc $TTC_V $BOARD cp target:$BOARD_DIR/big-random-data $RECV_DIR >$RESULTS
    RCODE=$?
    end_time=$(date +"%s.%N")

    HAVE_FILE=
    if [ $RCODE = "0" ] ; then
       if [ -f $RECV_DIR/big-random-data ] ; then
           if diff -a $SEND_DIR/big-random-data $RECV_DIR/big-random-data >/dev/null ; then
               succeed "$desc"
               HAVE_FILE=1
           else
               rm -f $RESULTS
               fail "$desc" "file does not match original"
           fi
       else
           rm -f $RESULTS
           fail "$desc" "file not found in local dir"
       fi
    else
        fail "$desc" "Error running ttc cp"
    fi
fi

#--------------------------------------------
THRESHOLD=5
desc="time to get 1M file is less than $THRESHOLD seconds"
if [ -z "$HAVE_FILE" ] ; then
    # do a skip
    fail "$desc" "SKIP - missing file for test"
else
    duration=$(python3 -c "print('%.2f' % ($end_time - $start_time))")
    dur_int=$(python3 -c "print(int($duration))")

    echo "# File copy (get) took $duration seconds"
    if [ $dur_int -lt $THRESHOLD ] ; then
        succeed "$desc"
    else
        fail "$desc"
    fi
fi

cleanup

echo "Done."

exit 0

