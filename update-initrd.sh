#/bin/bash
# update-initrd.sh
#
# note: this script is racy - it uses global temp file names
#
#set -x

usage() {
   cat <<HERE
Usage: update-initrd.sh [-h] <ref-initrd> <new-initrd>

This scripts uses an existing Ubuntu initrd and a set of
kernel modules, to build a new Ubuntu initrd.

<ref-initrd> is a file or path to an existing reference initrd
<new-initrd> is a file or path to the output initrd

-h    Show this usage help

If either paths have a colon in them, it is interpreted as
the form: <target>:<path> where the path is on the indicated
target, and can be retrieved or put with 'ttc cp'

\$KBUILD_OUTPUT has the path to kernel build directory, with the
new kernel modules in lib/modules/\${kernel-version}

The kernel-version must match the version of the kernel to be booted
on the target.

Here is an example of use of this script to provision a new initrd on
a board called 'min1'.  Note that the newly created initrd will be
called 'test_initrd', and placed directly in the board's /boot directory.
 $ update-initrd.sh min1:/boot/initrd.img-4.13.0-38-generic min1:/boot/test_initrd
HERE
   exit 1
}

if [ -z $1 ] ; then
    echo "Error Missing reference initrd path"
    usage
fi

if [ "$1" = "-h" ] ; then
    usage
fi

if [ -z $2 ] ; then
    echo "Error Missing output initrd path"
    usage
fi

# remove any dirs from previous run
rm -rf /tmp/ref_initrd /tmp/initrd_modlist /tmp/initrd_root \
    /tmp/new_initrd /tmp/new_initrd.gz

REF_INITRD_PATH=$1
OUT_INITRD_PATH=$2

ABS_BUILD_DIR=$(realpath $KBUILD_OUTPUT)

# retrieve reference initrd for operations
# check for path with colon
echo "Retrieving reference initrd from $REF_INITRD_PATH"
if [[ $REF_INITRD_PATH = *":"* ]] ; then
    IFS=":"  read -ra parts <<< ${REF_INITRD_PATH}
    TARGET=${parts[0]}
    REF_PATH=${parts[1]}
    ttc $TARGET cp target:${REF_PATH} /tmp/ref_initrd
else
    cp ${REF_INITRD_PATH} /tmp/ref_initrd
fi

# extract the initrd
echo "Extracting reference initrd..."
mkdir /tmp/initrd_root
pushd /tmp/initrd_root
gzip -dc </tmp/ref_initrd | cpio -i

# replace modules
echo "Replacing modules, from $ABS_BUILD_DIR/lib/modules"
rm -rf /tmp/initrd_root/lib/modules/*
cp -a $ABS_BUILD_DIR/lib/modules/* /tmp/initrd_root/lib/modules

# Only copy modules that were present in reference image
#pushd $ABS_BUILD_DIR/lib/modules
#find . -type f >/tmp/initrd_modlist
#new_ver="$(echo *)"
#
#OLD_IFS=$IFS
#IFS=$'\n'
#for f in $(cat /tmp/initrd_modlist) ; do
#    cp --parents $f /tmp/initrd_root/lib/modules/$new_ver/$f
#done
#
#IFS=$OLDIFS
#popd

# rebuild the initrd
echo "Creating new initrd..."
find . | cpio --create --format='newc' >/tmp/new_initrd
popd
gzip /tmp/new_initrd

# copy new initrd to requested path
# check for path with colon
echo "Placing new initrd to $OUT_INITRD_PATH"
if [[ $OUT_INITRD_PATH = *":"* ]] ; then
    IFS=":"  read -ra parts <<< ${OUT_INITRD_PATH}
    TARGET=${parts[0]}
    REF_PATH=${parts[1]}
    ttc $TARGET cp /tmp/new_initrd.gz target:${REF_PATH}
else
    cp /tmp/new_initrd.gz $OUT_INITRD_PATH
fi

echo "Done!"
