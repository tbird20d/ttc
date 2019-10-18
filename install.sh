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

if [ ! -d "$dest_path" ] ; then
	echo "Error: destination path must be a directory"
	exit 1 ;
fi

# copy the main tool
echo "Copying ttc to ${dest_path}..."
cp ${src_path}/ttc ${dest_path}

utils_file_list="telnet_exec \
	ssh_exec \
	powerswitch-cycle \
	powerswitch-set \
	update-initrd.sh \
	get-lts \
	get-ubuntu-patches \
	teensy-usb.py"

echo "Copying utils to ${dest_path}..."
for f in $utils_file_list ; do
	cp ${src_path}/utils/${f} ${dest_path} ;
done
