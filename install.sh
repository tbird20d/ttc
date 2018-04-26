#!/bin/sh
#
# a very rudimentary install script for ttc
#

dest_path=$1
src_path=$(dirname $0)

if [ -z "$dest_path" ] ; then
	echo "Usage: install.sh <dest_dir>" ;
	exit 1 ;
fi

file_list="ttc telnet_exec ssh_exec powerswitch-cycle \
	ttc_test_utils.py target-test.py powerswitch-set"

echo "Copying from ${src_path} to ${dest_path}..."
for f in $file_list ; do 
	cp ${src_path}/${f} ${dest_path} ;
done
