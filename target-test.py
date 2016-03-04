#!/usr/bin/python
#
# target-test.py - python routine to test a target configuration under ttc
#
# To Do for target-test.py
# * make sure that no existing env. vars are set to conflict with our target
#
# BUGS:
#  * failure of telnet_exec (ttc run) is not handled properly:
#
# OUTLINE:
# 001 make sure the target is listed
# 002 get target info and validate it
# 003 make sure you can get the kernel source
#   * report on the version of the kernel source
# 004 make sure you can build the kernel
# 005 make sure you can install the kernel
# 006 make sure you can get the default kernel configuration
# 007 make sure you can change the kernel configuration
# 008 make sure you can reboot the board
# 009 make sure that the board boots with the new kernel
#   * make sure that the running kernel is the one newly built
# 010 make sure that you can copy a file to the target
# 011 make sure that you can copy a file from the target
# 012 make sure that you can execute a command on the target
# 013 make sure that you can get an interactive console on the target
# 014 make sure you can apply a patch to the kernel
# 015 make sure you can compile a small program for the target
#   * compile it, install it (with copy), and run it
# 016 make sure you can change the kernel command line

MAJOR_VERSION = 1
MINOR_VERSION = 0
REVISION      = 0

import os, sys
import re, time, random
import commands
import ttc_test_utils

######################################
# Define some globals for this test suite

test_suite_name="TARG"
src_dir = "test-linux"
test_data_dir = "../test-data"

######################################
# Define some convenience classes and functions

def usage():
	prog_name = os.path.basename(sys.argv[0])
	print """Usage: %s [-h] <target>

where <target> is the name of the target to be used with
the 'ttc' command.

%s is a program to test whether the ttc tool is working properly
with a specified target.  It executes several ttc commands, and
tests the results.  If any tests fail, the problems should be
fixed before executing any other automated tools which use ttc.

-h	show this usage help
-V	show version information
""" % (prog_name, prog_name)

def test_setup(test_run):
	# test run prep
	print "Doing test preparation for %s tests..." % test_suite_name

	# make test build dir
	build_dir = "test-build/%s" % test_run.target
	rcode = test_run.do_command("install -d %s" % build_dir, 1)

	# set KBUILD_OUTPUT environment variable to build directory
	# Use a relative path from the kernel source directory, which
	#   will be one dir down from here.
	build_dir = "../test-build/%s" % test_run.target
	os.environ["KBUILD_OUTPUT"]=build_dir

	test_run.build_dir = build_dir


#############################################
# TARG-002 get target info and validate it
def test_002(test_run):
	target = test_run.target
	test_run.set_id("002", "get target info")
	print "Running test %s..." % test_run.id

	cmd = "ttc %s info" % target
	(rcode, result) = test_run.do_command_result(cmd)
	if rcode:
		test_run.failure("Could not get info for target '%s'" % target, result)
	
	# FIXTHIS - how to validate 'ttc info' result??

	test_run.success("Retrieved info for target '%s'" % target, result)

	cmd = "ttc %s info -v" % target
	(rcode, result) = test_run.do_command_result(cmd)
	if rcode:
		test_run.failure("Could not get verbose info for target '%s'" % target, result)

	# FIXTHIS - how to validate verbose information??
	test_run.success("Retrieved verbose info for target", result)

	cmd = "ttc %s info -n kimage" % target
	(rcode, result) = test_run.do_command_result(cmd)
	if rcode:
		test_run.failure("Could not get kernel image name for target '%s'" % target, result)

	kimage = result

	# check that the kernel name is one of the 'normal' values
	test_run.result_out("kernel image name is '%s'" % kimage)
	if result not in ["vmlinux", "vmlinuz", "bzImage", "uImage", "cuImage.sequoia"]:
		test_run.failure("Kernel image name is unexpected")
	else:
		test_run.success("Kernel image name is OK")
	
#############################################
# TARG-003
# 003 make sure you can get the kernel source
#   * report on the version of the kernel source
#
def test_003(test_run):
	test_run.set_id("003", "get kernel source")

	# SPECIAL - test for 'gk_marker' to avoid long delays when the 
	# test is re-run (which happens often during test development)

	# auto-detect that kernel is already present in src_dir
	# and skip the get_kernel automatically
	rcode = test_run.do_command('test -f %s/gk_marker' % src_dir)
	extra_data = ""
	if rcode:
		test_run.do_ttc("get_kernel -o %s" % src_dir, 1)
		test_run.do_command('echo "get_kernel completed" >%s/gk_marker' % src_dir)
	else:
		extra_data = "*** Skipping get_kernel (get_kernel marker found)"
		print extra_data

	# check for success
	# try to change to source directory
	try:
		os.chdir(src_dir)
	except:
		test_run.failure("Could not switch to kernel source directory after 'get_kernel'")
		sys.exit(1)

	# look for some 'normal' files at the root of the kernel source
	if not os.path.isfile('MAINTAINERS') or not os.path.isfile('Kbuild'):
		test_run.failure("Missing key files in kernel source directory after 'get_kernel'")
		sys.exit(1)
	
	# read Makefile, and get kernel version
	makelines = open("Makefile").readlines()
	version = 0
	minor = 0
	revision = 0
	extra = ""
	for line in makelines:
		if not version and line.startswith('VERSION'):
			version = line.split('=')[1].strip()
		if not minor and line.startswith('PATCHLEVEL'):
			minor = line.split('=')[1].strip()
		if not revision and line.startswith('SUBLEVEL'):
			revision = line.split('=')[1].strip()
		if not extra and line.startswith('EXTRAVERSION'):
			extra = line.split('=')[1].strip()
	ver_str = "%s.%s.%s%s" % (version, minor, revision, extra)
	test_run.result_out("Kernel version is %s" % ver_str)
	test_run.success("Retrieved kernel source OK", extra_data)

#############################################
# TARG-004 make sure you can get the default kernel configuration
#
def test_004(test_run):
	test_run.set_id("004", "get default kernel configuration")
	print "Running test %s..." % test_run.id

	config_filename = os.path.join(test_run.build_dir, ".config")
	# first, remove old configuration, if present
	
	if os.path.isfile(config_filename):
		os.unlink(config_filename)
		if os.path.isfile(config_filename):
			test_run.failure("Could not remove pre-existing kernel config file from build dir.")
			sys.exit(1)

	# get default configuration
	rcode = test_run.do_ttc("get_config", 1)

	# verify that the configuration was placed in the build directory
	if not os.path.isfile(config_filename):
		test_run.failure("Could not get default kernel configuration for target")
		sys.exit(1)
	else:
		test_run.success("Got default kernel configuration for target")

	# FIXTHIS - should validate the the configuration has no invalid junk
	# how???


#############################################
# TARG-005 make sure you can build the kernel
#
def test_005(test_run):
	test_run.set_id("005", "build kernel")
	print "Running test %s..." % test_run.id

	skipping = 0
	if skipping:
		print "*** Skipping kernel build"
		return

	kernel_filename = os.path.join(test_run.build_dir, "vmlinux")

	# remove existing kernel file, if present
	if os.path.isfile(kernel_filename):
		os.unlink(kernel_filename)
		if os.path.isfile(kernel_filename):
			test_run.failure("Could not remove pre-existing kernel image file from build dir.")
			sys.exit(1)
	
	# 4. build kernel
	rcode = test_run.do_ttc("kbuild")
	if rcode:
		test_run.failure("Could not build kernel")

	# there should be a vmlinux at root of build directory.
	if not os.path.isfile(kernel_filename):
		test_run.failure("No 'vmlinux' found after build")
	else:
		test_run.success("Found 'vmlinux' after build")

#############################################
# TARG-006 make sure you can install the kernel and reboot
#
def test_006(test_run):
	test_run.set_id("006", "install kernel, reboot and run command")
	print "Running test %s..." % test_run.id

	# set the localversion to something unique
	test_run.set_localversion()
	rcode = test_run.do_ttc("kbuild")

	# test to make sure localversion was built into local kernel image
	id_str = test_run.kernel_id
	rcode = test_run.do_command("grep %s $KBUILD_OUTPUT/vmlinux" % id_str)
	if rcode:
		test_run.failure("Could not build kernel with unique identifier '%s'" % id_str)
		return

	# install kernel
	rcode = test_run.do_ttc("kinstall", 1)
	if rcode:
		test_run.failure("Could not install kernel")

	# FIXTHIS - can't detect correct kernel installation without rebooting
	# the board.  This tests more than just kernel installation.

	# reset the board - use strongest reboot possible
	test_run.reset_target("reboot")

	if test_run.check_localversion():
		test_run.success("Kernel %s installed and booted on board" % test_run.kernel_id)
	else:
		test_run.failure("Could not verify kernel running on target board")

	test_run.run_on_target("dmesg >/tmp/dmesg.boot.006")


#############################################
# TARG-007 make sure you can change the kernel configuration
#
def test_007(test_run):
	test_run.set_id("007", "change kernel configuration")
	print "Running test %s..." % test_run.id

	rcode = test_run.do_ttc("set_config CONFIG_PRINTK_TIME=y", 1)
	rcode = test_run.do_ttc("set_config CONFIG_LOG_BUF_SHIFT=17", 1)
	# rcode = test_run.do_ttc("set_config CONFIG_PRESET_LPJ=%s" % lpj, 1)

	(rcode, result) = test_run.do_make_oldconfig()
	print result

	test_run.check_config("CONFIG_PRINTK_TIME", "y")

	# set the localversion to something unique
	test_run.set_localversion()
	rcode = test_run.do_ttc("kbuild")

	# test to make sure localversion was built into local kernel image
	id_str = test_run.kernel_id
	rcode = test_run.do_command("grep %s $KBUILD_OUTPUT/vmlinux" % id_str)
	if rcode:
		test_run.failure("Could not build kernel with unique identifier '%s'" % id_str)
		return

	# install kernel
	rcode = test_run.do_ttc("kinstall", 1)
	if rcode:
		test_run.failure("Could not install kernel")

	# reset the board - use strongest reboot possible
	test_run.reset_target("reboot")

	if not test_run.check_localversion():
		test_run.failure("Could not verify kernel running on target board")

	# check for printk times format output
	rcode, result = test_run.run_on_target("dmesg")
	if rcode:
		test_run.failure("Error collecting results from 'dmesg'", result)
		return
	result_list = result.split("\n")

	# look for 3 samples
	sample_locs = [4,7,11]
	samples = []

	printk_format_ok = 1
	for i in sample_locs:
		sample_line = result_list[i]

		# work around busybox bug leaving leading kernel msg level tag
		if re.match("\<[0-9]\>", sample_line):
			sample_line = sample_line[3:]

		if not re.match("\[ *[0-9]+\.[0-9]+\] ", sample_line):
			printk_format_ok = 0
			test_run.failure("Didn't find printk time format on dmesg line '%s'" % sample_line)

	if printk_format_ok:
		test_run.success("Successfully modified kernel configuration (with PRINTK_TIMES=y)")

	test_run.run_on_target("dmesg >/tmp/dmesg.boot.007")
	# FIXTHIS - should compare with: "/tmp/dmesg.boot.006" to make sure printk-times wasn't set before

	# reset config
	# get default configuration
	rcode = test_run.do_ttc("get_config", 1)

	# set the localversion to something unique
	test_run.set_localversion()
	rcode = test_run.do_ttc("kbuild")

	# install kernel
	rcode = test_run.do_ttc("kinstall", 1)
	if rcode:
		test_run.failure("Could not install kernel")

#############################################
# TARG-008 make sure you can reboot target
#
# check for two failure conditions, for both reset and reboot:
# 1) target was running, and after reset it never comes back up
#   this is a case of hanging on the reset, which is common when
#   a soft reset ('ttc run reboot') is used.
# 2) target was running, and it continued running despite the reset request
#   This is another common case for when soft reset is used.
def test_008(test_run):
	test_run.set_id("008", "reset and reboot target")
	print "Running test %s..." % test_run.id

	# FIXTHIS - this test assumes the target is running, on entry

	print "Waiting a bit for target to accumulate uptime..."
	time.sleep(40)

	# get uptime
	time1 = time.localtime()
	rcode, result1 = test_run.run_on_target("cat /proc/uptime")
	test_run.reset_target("reset")

	# see if target resets
	rcode = test_run.wait_for_target_to_boot()
	if rcode:
		test_run.failure("Target board did not reset properly")
	else:
		# get uptime after resetting
		time2 = time.localtime()
		rcode, result2 = test_run.run_on_target("cat /proc/uptime")

		# parse results here
		t1 = float(result1.split()[0])
		t2 = float(result2.split()[0])
		test_run.result_out("uptime before reset was %s, and after reset it is %s" % (t1, t2))
		# check if t2 < t1  If so, the client reset

		if t2 < t1:
			test_run.success("Target board reset properly")
		else:
			test_run.failure("Target board did not reset properly")
		

	# now test rebooting
	test_run.reset_target("reboot")
	rcode = test_run.wait_for_target_to_boot()
	if rcode:
		test_run.failure("Target board did not reboot properly")
	else:
		print "Waiting a bit for target to accumulate uptime..."
		time.sleep(40)

		# get uptime1
		time1 = time.localtime()
		rcode, result1 = test_run.run_on_target("cat /proc/uptime")
		test_run.reset_target("reboot")

		# get uptime after rebooting
		time2 = time.localtime()
		rcode, result2 = test_run.run_on_target("cat /proc/uptime")

		# parse results here
		t1 = float(result1.split()[0])
		t2 = float(result2.split()[0])
		test_run.result_out("uptime before reboot was %s, and after reboot it is %s" % (t1, t2))
		# check if t2 < t1  If so, the client reset

		# get uptime after rebooting
		time2 = time.localtime()
		rcode, result2 = test_run.run_on_target("uptime")

		# check if t2 < t1  If so, the client rebooted
		if t2 < t1:
			test_run.success("Target board rebooted properly")
		else:
			test_run.failure("Target board did not reboot properly")


# 009 make sure that the board boots with the new kernel
#   * make sure that the running kernel is the one newly built

#############################################
# TARG-010 make sure that you can copy a file to the target
#
def test_010(test_run):
	test_run.set_id("010", "copy file to target")
	print "Running test %s..." % test_run.id

	testfile_name = "/tmp/test_010_file"

	# create a test file with unique content
	id_str = "unique_id=%s\n" % random.randint(1,10000)
	fd = open(testfile_name, "w")
	fd.write(id_str)
	fd.close()

	# copy file to target
	rcode = test_run.do_ttc("cp %s target:%s" % (testfile_name, testfile_name))

	# verify file is present on target
	cmd = "cat %s" % testfile_name
	rcode, result = test_run.run_on_target(cmd)
	if rcode:
		test_run.failure("Could not '%s' on target" % cmd)
		return

	print "id_str=", id_str.strip()
	print "result=", result.strip()

	# compare original and copied files
	if result.strip() == id_str.strip():
		test_run.success("File was successfully copied to target")
	else:
		test_run.success("File was successfully copied to target")

	# clean up
	os.unlink(testfile_name)
	rcode, result = test_run.run_on_target("rm %s" % testfile_name)

#############################################
# TARG-011 make sure that you can copy a file from the target
#
def test_011(test_run):
	test_run.set_id("011", "copy file from target")
	print "Running test %s..." % test_run.id

	testfile_name = "/tmp/test_011_file"

	# create a test file with unique content on the target
	id_str = "unique_id=%s" % random.randint(1,10000)
	cmd = 'echo "%s" >%s' % (id_str, testfile_name)
	rcode = test_run.run_on_target(cmd)

	# copy file from the target
	rcode = test_run.do_ttc("cp target:%s %s" % (testfile_name, testfile_name))
	if rcode:
		test_run.failure("File was not copied correctly from target. 'ttc cp...' failed.")

	try:
		fd = open(testfile_name, "r")
		content = fd.read()
		fd.close()
	except:
		test_run.failure("Could not read content of file read from target")
		return
		

	print "id_str=", id_str.strip()
	print "content=", content.strip()

	# compare original and copied files
	if content.strip() == id_str.strip():
		test_run.success("File was successfully copied from target")
	else:
		test_run.failure("Content of file copied from target was incorrect")

	# clean up
	os.unlink(testfile_name)
	rcode, result = test_run.run_on_target("rm %s" % testfile_name)
	
# 012 make sure that you can execute a command on the target
# 013 make sure that you can get an interactive console on the target

# 014 make sure you can apply a patch to the kernel
# 015 make sure you can compile a small program for the target
#   * compile it, install it (with copy), and run it

#############################################
# TARG-016 make sure that you can change the kernel command line
#
def test_016(test_run):
	test_run.set_id("016", "change kernel command line")
	print "Running test %s..." % test_run.id

	rcode = test_run.do_ttc("get_config")
	if rcode:
		test_run.failure("Could not get default config")
		return

	# try to set CONFIG_CMDLINE_BOOL (required on x86 to set CONFIG_CMDLINE)
	# don't fail if it's missing.
	rcode = test_run.do_ttc('set_config CONFIG_CMDLINE_BOOL=Y', 0)

	rcode = test_run.do_ttc('set_config "CONFIG_CMDLINE+=\\" quiet\\""', 1)
	if rcode:
		test_run.failure("Could not set 'quiet' on kernel command line")
		return

	test_run.do_make_oldconfig()

	# check for CMDLINE in .config file
	build_dir = os.environ["KBUILD_OUTPUT"]

	# read .config 
	cmd = 'grep CONFIG_CMDLINE %s/.config' % build_dir
	(rcode, result) = commands.getstatusoutput(cmd)
	if rcode:
		test_run.failure("Couldn't find CMDLINE in .config file")
		return

	# check for quiet in CMDLINE in .config file
	if not re.match(".*quiet", result):
		test_run.failure("Couldn't find 'quiet' in CMDLINE in .config file")
		return

	# set the localversion to something unique
	# then build kernel
	test_run.set_localversion()
	rcode = test_run.do_ttc("kbuild")
	if rcode:
		test_run.failure("Could not build kernel")

	# install kernel
	rcode = test_run.do_ttc("kinstall", 1)
	if rcode:
		test_run.failure("Could not install kernel")

	# reboot the board
	test_run.reset_target("reboot")

	if test_run.check_localversion():
		test_run.success("Kernel %s installed and booted on board" % test_run.kernel_id)
	else:
		test_run.failure("Could not verify kernel running on target board")
		return

	# see if option was on kernel command line from dmesg
	rcode, result = test_run.run_on_target('dmesg | grep "command line:"')
	if rcode:
		test_run.failure("Could not verify command line on target")
		return

	if not re.match(".*quiet", result):
		test_run.failure("Could not find 'quiet' in command line on target")
		return
		
	test_run.success("Found 'quiet' on command line on target")

def main():
	# get list of valid targets
	(rcode, result) = commands.getstatusoutput('ttc list -q')
	tlist = result.split("\n");
	if rcode:
		print "Error: Problem running 'ttc list'"
		sys.exit(1)

	# Parse the command line
	if len(sys.argv)<2:
		print "Error: missing target to run test on."
		usage()
		print "Available targets are:"
		for t in tlist:
			print "   %s" % t
		print
		sys.exit(1)

	if '-h' in sys.argv:
		usage()
		sys.exit(1)

	if '-V' in sys.argv:
		print "target-test.py Ver. %d.%d.%d" % (MAJOR_VERSION, MINOR_VERSION, REVISION)
		sys.exit(1)

	target = sys.argv[1]

	# FIXTHIS - make sure there are no conflicts - check for existing
	# TTC_TARGET environment variable
	if os.environ.has_key("TTC_TARGET"):
		print "Error: found TTC_TARGET in environment."
		print "Please do not run this test inside an existing ttc target environment."
		print "Aborting test."
		sys.exit(1)

	test_run = ttc_test_utils.test_run_class(test_suite_name, target)

	# make directory for test output
	# remove leading ../ from test_data_dir, since we haven't changed
	# to the kernel source dir yet
	test_run.do_command("install -d %s" % test_data_dir[3:], 1)

	test_run.start_log(test_data_dir[3:])

	# start testing now
	####################################
	# TARG-001 - verify target is in list
	test_run.set_id("001", "verify target is in 'ttc list'")
	print "Running test %s..." % test_run.id

	if target not in tlist:
		test_run.failure("Error: target '%s' not found in ttc configuration" % target)
		print "\n###########################################"
		print "Results summary:"
		test_run.show_summary_results()
		sys.exit(1)

	test_run.success("target '%s' is in 'ttc list'" % target)

	# set up test directories
	test_setup(test_run)

	# run remainder of tests
	test_002(test_run)
	test_003(test_run)
	# cwd is now the kernel source directory

	test_004(test_run)
	test_005(test_run)
	test_006(test_run)
	test_007(test_run)
	test_008(test_run)
	test_010(test_run)
	test_011(test_run)
	test_016(test_run)

	test_run.close_log()

	print "\n###########################################"
	print "Results summary:"
	test_run.show_summary_results()

if __name__=="__main__":
	main()
