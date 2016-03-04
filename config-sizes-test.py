#!/usr/bin/python
#
# config-sizes-test.py - python routine to generate size data from kernel
#
# To Do for config-sizes-test.py
# * set up crontab to produce results daily
# * save and show subsystem sizes (net/builtin.o, etc.)
# * determine and show kernel description string
#   * alp patch level
#   * kernel version
# * highlight lines in table for linux-tiny options
# * get free_mem earlier in bootup (to avoid fluctuations)
#   * use grabserial to capture bootup messages
#   * use bootup messages to diagnose boot failures 
#
# To Do for config options:
# * make sure smallest IO scheduler is in the smallest config
# * make it possible to disable SYSCTL
# * make it possible to disable MODULES
# * make it possible to disable CRYPTO
# * make it possible to disable DIRECTIO
# * (i386) find out why INLINE_THREADINFO cannot be configured
# * find out why setting NR_LDISCS=1 uses more runtime memory
# * find out why setting PANIC=n uses more runtime memory
# * find out why setting MAX_SWAPFILES_SHIFT=0 uses more runtime memory
# * find out why setting XATTR=n uses more runtime memory
#
# To Do for test framework:
# * show sub-command output if "-v" is specified
#   * show it interactively (while it is being collected??)
# * make a convenience routine to perform "ttc" commands
# Done:
# * populate option_list with config options to test
#
# BUGS:
#
# CHANGELOG:
# 0.8.1 - reorganize code to use same routine for baseline, baseline-popped,
#         and smallest.  Use "ttc reboot" if "ttc reset" fails.
#         Output the log file as we go (to conserve partial results in
#         case of a program crash).
# 0.8.0 - Move wiki-page generation to a separate program.
# 0.7.9 - Add initial support for runtime testing.  Change the way reporting
#         is done to support better summaries in the log. Change naming so
#	  that baseline is baseline-popped and baseline-tiny is "baseline"
#	  For a kernel.org kernel, baseline-popped is the same as baseline.
#	  For a -tiny kernel, baseline-popped should be the same as kernel.org
#	  and baseline is with linux-tiny patches applied.  Config differences
#	  are done against config.baseline.  Wrote code to collect size
#	  information into a data dictionary, and to output a moin table
#	  at the end.
# 0.7.8 - Adjust output files to remove "CONFIG_" prefix
# 0.7.7 - add -t flag to perform tiny-specific testing
# 0.7.6 - add new options for tiny patches
#         LINUXTINY_DO_UNINLINE, PANIC, FULL_PANIC, CRC32_TABLES,
#         INLINE_THREADINFO, MEMPOOL, CONSOLE_TRANSLATIONS
# 0.7.5 - convert baseline to baseline (popped), and create new
#         baseline-tiny (with patches pushed).  This is so I can measure
#         the effect of linux-tiny patches which don't have a CONFIG option
#         (by comparing vmlinux.baseline and vmlinux.baseline-tiny)
# 0.7.4 - add new options for latest up-ported tiny patches
#         IGMP, IDW_HWIFS, SERIAL_PCI, PCI_QUIRKS, NET_SK_FILTER, etc.
# 0.7.3 - allow omitting the baseline build.
# 0.7.2 - add code to indicate which symbol number we're on.
#

import os, sys
import commands
import re
import time
import random

MAJOR_VERSION = 0
MINOR_VERSION = 8
REVISION = 1

######################################
# Define some globals for this test suite

test_suite_name="Size-test"
src_dir = "test-linux"
test_data_dir_top = "../test-data"
default_wiki_path = "oak:/usr/share/moin/alpwiki/data/text/ConfigSizeTestResults"

yes_no_options = [
	"BASE_FULL", "NET_SMALL", "CC_FUNIT_AT_A_TIME",
	"LINUXTINY_DO_UNINLINE",
	"PANIC", "FULL_PANIC",
	"SYSFS_DEPRECATED",
	"SYSFS",
	"ETHTOOL", "INETPEER", "NET_SK_FILTER", "NET_DEV_MULTICAST",
	"IGMP", "IP_MULTICAST", "BINFMT_SCRIPT", "BINFMT_ELF_AOUT",
	"PRINTK", "BUG", "ELF_CORE", "PROC_KCORE", "SYSENTER", "AIO", "XATTR",
	"FILE_LOCKING", "DIRECTIO", "KALLSYMS", "KALLSYMS_ALL",
	"SHMEM", "SWAP", "SYSVIPC",
	"SYSVIPC_SYSCTL", "PROC_SYSCTL", "SYSCTL_SYSCALL",
	"PROC_FS",
	"UID16",
	"MODULES", "ISA", "KMOD",
	"DAB", "VGA_CONSOLE",
	"USB", "HID", "PCI", "XIP_KERNEL",
	"BLK_DEV_LOOP", "BLK_DEV_RAM",
	"IOSCHED_AS", "IOSCHED_DEADLINE", "IOSCHED_CFQ",
	"IP_PNP", "IP_PNP_DHCP",
	"IDE", "SCSI",
	"EXT2_FS", "EXT3_FS", "INOTIFY", "AUTOFS_FS", "AUTOFS4_FS", "NFS_FS",
	"DLM", "PROFILING", "KPROBES",
	"ENABLE_MUST_CHECK",
	"UNUSED_SYMBOLS", "DEBUG_KERNEL", "DOUBLEFAULT",
	"CRYPTO", "SERIAL_PCI", "PCI_QUIRKS",
	"CRC32_TABLES",
# threadinfo-ool.patch is bitrotted as of 2007-10
#	"INLINE_THREADINFO",
	"MEMPOOL", "CONSOLE_TRANSLATIONS",
]

option_list = [("MAX_SWAPFILES_SHIFT", ('5','1','0')),
	("NR_LDISCS", ('16','1')),
	("MAX_USER_RT_PRIO", ('100', '5')),
	# 12 is the smallest LOG_BUF_SHIFT allowed
	("LOG_BUF_SHIFT", ('17', '14', '12')),
	("IDE_HWIFS", ('0', '16', '1')),
	#("SLAB",('n',('y',[("SLUB",'n'),("SLOB",'n')]) )),
	("SLUB",('n',('y',[("SLAB",'n'),("SLOB",'n'),("SLUB_DEBUG",'n')]) )),
	("SLOB",('n',('y',[("SLAB",'n'),("SLUB",'n')]) )),
	("SYSCTL",('y',('n',[("SYSVIPC_SYSCTL",'n'),("PROC_SYSCTL",'n'),
		("SYSCTL_SYSCALL",'n')]) )),
]

test_list = [
	("SYSCTL",('y',('n',[("SYSVIPC_SYSCTL",'n'),("PROC_SYSCTL",'n'),
		("SYSCTL_SYSCALL",'n')]) )),
]

small_config_list = [
	("BASE_FULL", "n"), ("NET_SMALL","y"),
	("LINUXTINY_DO_UNINLINE","y"),
	("CC_FUNIT_AT_A_TIME","y"),
# next one has a compile problem on OSK
#	("PANIC","n"),
	("SYSFS_DEPRECATED","n"),
	("SYSFS","n"),
	("ETHTOOL", "n"),
	("INETPEER", "n"), ("NET_SK_FILTER", "n"),
	("NET_DEV_MULTICAST", "n"), ("IGMP", "n"), ("BINFMT_ELF_AOUT", "n"),
	("PRINTK","n"), ("PRINTK_FUNC","n"),
	("BUG","n"), ("ELF_CORE","n"), ("PROC_KCORE","n"),
	("SYSENTER", "n"), ("AIO","n"),
	("XATTR","n"), 
	("FILE_LOCKING","n"),
	("DIRECTIO","n"),
	("MAX_SWAPFILES_SHIFT","0"), ("NR_LDISCS","5"), ("KALLSYMS","n"),
	("SHMEM","n"), ("SWAP","n"), ("SYSVIPC","n"),
	("PROC_SYSCTL","n"), ("SYSCTL_SYSCALL","n"), ("SYSCTL", "n"),
	("PROC_FS","n"),
	("LOG_BUF_SHIFT","12"), ("UID16", "n"),
	("MODULES", "n"), ("DAB","n"), ("VGA_CONSOLE","n"),
	("ISA", "n"), ("KMOD", "n"), ("PCI", "n"), ("USB", "n"),
	("HID", "n"), ("XIP_KERNEL", "n"),
	("BLK_DEV_LOOP", "n"), ("BLK_DEV_RAM", "n"),
	("BLK_DEV_RAM_COUNT", "2"), ("BLK_DEV_RAM_SIZE", "1024"),
	("IOSCHED_AS","n"), ("IOSCHED_DEADLINE", "y"), ("IOSCHED_CFQ", "n"),
	("IP_PNP", "n"), ("IP_PNP_DHCP", "n"),
	("IDE", "n"), ("SCSI", "n"),
	("EXT2_FS", "n"), ("EXT3_FS", "n"), ("INOTIFY", "n"),
	("AUTOFS_FS", "n"), ("AUTOFS4_FS", "n"), ("NFS_FS", "n"),
	("DLM", "n"), ("PROFILING", "n"), ("KPROBES", "n"),
	("ENABLE_MUST_CHECK", "n"), ("UNUSED_SYMBOLS", "n"),
	("DEBUG_KERNEL", "n"), ("DOUBLEFAULT", "n"),
	("CRYPTO", "n"), ("SERIAL_PCI", "n"), ("PCI_QUIRKS", "n"),
	("CRC32_TABLES", "n"), ("INLINE_THREADINFO","n"),
	("MEMPOOL","n"), ("CONSOLE_TRANSLATIONS","n"),
	("SLOB","y"),
]

######################################
# Define some convenience classes and functions

def usage():
	print """Usage: %s <options> <target>

where <options> are shown below, and <target> is the name of the
target for the 'ttc' command,

By default, this program builds a baseline kernel, several kernels
in alternative configurations, and a "smallest-configuration" kernel.

 -h     Show this usage help
 -c     Continue building from a previous run.  That is, if the output
        files for an option already exist, skip the build for those options.
 -a-	Omit building the configuration alternatives.
        (Only make the baseline and smallest kernels)
 -b-    Omit building the baseline configuration.
 -s     Make the smallest kernel
 -p     Make a "popped" kernel (with any quilt-style patches removed)
 -r     Perform runtime test of free memory
 -o <config_exp>  Specify a one-shot build, for the config option specified.
 -t     Build the 'test' options, instead of the default option list.
 -V     Show version information

For a one-shot build, the program will build the baseline kernel,
and then perform alternate builds, altering only one specified
CONFIG variable.  The config expression can be a simple or compound.
Some examples are:
 -o AIO=y|n
 -o AIO
 -o LOG_BUF_SHIFT=9|11|14|17

An equal sign separates the option name from the list of values to try.
Values are separated from each other by vertical bars.  If the equal
sign and values are omitted, then the values "y" and "n" are used.
The first two examples above are equivalent.
""" % os.path.basename(sys.argv[0])

class test_run_class:
	def __init__(self, suite_name, target):
		self.suite_name = suite_name
		self.target = target
		self.set_id('001')
		self.results_list = []
		self.time = time.localtime()
		self.data = {}
		self.runtime_data = {}
		self.logfd = None

		rcode, result = do_command_result("hostname")
		self.hostname = result.strip()

	def set_id(self, id):
		self.id = self.suite_name+"-"+id

	def save_result_str(self, rtype, msg, extra_data):
		# IDEA: could save timestamp here also
		self.results_list.append((self.id, rtype, msg, extra_data))
		if self.logfd:
			out_msg = "[TEST: %s] %s - %s" % (self.id, rtype, msg)
			self.logfd.write(out_msg+"\n")
			if extra_data:
				self.logfd.write(extra_data+"\n")
			self.logfd.flush()

	def start_log(self, test_data_dir):
		t = time.strftime("%Y.%m.%d-%H:%M:%S", self.time)
		logfilename = test_data_dir + "/%s-%s-%s.log" % \
			(self.suite_name, self.target, t)
		self.logfd = open(logfilename, "w")
		fd = self.logfd
		fd.write("Details:\n")
		fd.write("------------------\n\n")
		fd.write("%s test results\n" % self.suite_name)
		fd.write("time = %s\n" % time.asctime(self.time))
		fd.write("target = %s\n" % self.target)
		fd.write("host = %s\n" % self.hostname)
		fd.write("------------------\n\n")
		fd.flush()

	def close_log(self, summary=1):
		fd = self.logfd
		if not fd:
			return

		if summary:
			fd.write("Summary:\n")
			self.write_summary_results(fd)
			fd.write("------------------\n\n")

		fd.close()
		self.logfd = None

	def write_summary_results(self, fd):
		for id, rtype, msg, extra_data in self.results_list:
			out_msg = "[TEST: %s] %s - %s" % (id, rtype, msg)
			fd.write(out_msg+"\n")

	def show_summary_results(self):
		self.write_summary_results(sys.stdout)


# maybe these should be test_run_class methods???
# (but it makes actual test code more verbose)
def result_out(test_run, msg, extra_data=''):
	test_run.save_result_str("RESULT", msg, extra_data)

	out_msg = "[TEST: %s] Result - %s" % (test_run.id, msg)
	print out_msg
	sys.stdout.flush()

def success(test_run, msg, extra_data=''):
	test_run.save_result_str("SUCCESS", msg, extra_data)

	out_msg = "[TEST: %s] Success - %s" % (test_run.id, msg)
	print out_msg
	sys.stdout.flush()

def failure(test_run, msg, extra_data=''):
	test_run.save_result_str("FAILURE", msg, extra_data)

	out_msg = "[TEST: %s] Failure - %s" % (test_run.id, msg)
	print out_msg
	sys.stdout.flush()

def do_command(cmd, exception_on_error=0, ignore_error=0):
	print "  Executing '%s'" % cmd
	sys.stdout.flush()
	(rcode, result) = commands.getstatusoutput(cmd)
	if rcode and not ignore_error:
		err_str = 'Error running cmd "%s"' % cmd
		print err_str
		print 'command output=%s' % result
		sys.stdout.flush()
		if exception_on_error:
			raise ValueError, err_str
	return rcode

def do_command_result(cmd, exception_on_error=0, ignore_error=0):
	print "  Executing '%s'" % cmd
	sys.stdout.flush()
	rcode, result = commands.getstatusoutput(cmd)
	if rcode and not ignore_error:
		err_str = 'Error running cmd "%s"' % cmd
		print err_str
		print 'command output=%s' % result
		sys.stdout.flush()
		if exception_on_error:
			raise ValueError, err_str
	return rcode, result

def check_config(config, value):
	build_dir = os.environ["KBUILD_OUTPUT"]
	cmd = 'grep %s %s/.config' % (config, build_dir)
	(rcode, result) = commands.getstatusoutput(cmd)
	if rcode:
		print "Error grepping .config file"
		print "result=", result

	
	print "check_config cmd='%s'" % cmd
	print "check_config grep result=", result

	# now match a pattern for the desired value
	value_pat = value
	if value=="n":
		value_pat = ".*not set"
	if value=="y":
		value_pat = ".*%s=y" % config

	return re.match(value_pat, result)

def test_setup(test_run):
	global build_dir
	# prepare for a test run
	# 1. get kernel
	# 1.1 make build dir
	# 1.2 make test data dir
	# 2. get default config

	target = test_run.target

	print "Doing test preparation for %s tests..." % test_run.suite_name

	# auto-detect that kernel is already present in src_dir
	# and skip the get_kernel automatically
	rcode = do_command('test -f %s/gk_marker' % src_dir)
	if rcode:
		do_command("ttc %s get_kernel -o %s" % (target, src_dir), 1)
		do_command('echo "get_kernel completed" >%s/gk_marker' % src_dir)
	else:
		print "*** Skipping get_kernel (get_kernel marker found)"

	os.chdir(src_dir)
	build_dir = "../test-build/%s" % target
	os.environ["KBUILD_OUTPUT"]=build_dir
	do_command("install -d %s" % build_dir, 1)
	do_command("install -d %s" % test_data_dir, 1)

	# create baseline config, and save it
	do_command("ttc %s get_config" % target, 1)
	do_command("ttc %s set_config CONFIG_EMBEDDED=y" % target)
	do_oldconfig(target)
	do_command("cp %s/.config %s/config.baseline" % \
			(build_dir, test_data_dir))

# config-name should be one of: baseline, baseline-popped, or smallest
def test_kernel(test_run, config_name):
	global runtime_test

	test_run.set_id(config_name)
	print "Running test %s..." % test_run.id
	target = test_run.target
	build_dir = os.environ["KBUILD_OUTPUT"]

	# see if we should pop all the patches
	have_patches = os.path.exists("patches/series")
	if config_name=="baseline-popped" and have_patches:
		rcode, result = do_command_result("quilt pop -a")
		if rcode:
			failure(test_run, "Could not pop patches", result)
			do_command("quilt push -a")
			return

	# get baseline config
	do_command("cp %s/config.baseline %s/.config" % \
			(test_data_dir, build_dir))

	# set everything as small as possible
	if config_name=="smallest":
		for option, value in small_config_list:
			option = "CONFIG_"+option
			rcode = do_command("ttc %s set_config %s=%s" % \
				(target, option, value))

	do_oldconfig(target)

	# save off config for test script debugging
	if config_name!="baseline":
		do_command("cp %s/.config %s/config.%s" % \
			(build_dir, test_data_dir, config_name))

	# remove last kernel built, if any
	rcode = do_command("rm %s/vmlinux" % build_dir, 0, 1)

	# clear localversion for better ccache-ing
	clear_localversion(test_run)

	# build kernel
	rcode, result = do_command_result("ttc %s kbuild" % target)
	if rcode or not os.path.exists("%s/vmlinux" % build_dir):
		failure(test_run, "Could not build %s kernel" % config_name, result)
		return

	# get size data for baseline kernel
	save_size_data(test_run, "%s/vmlinux" % build_dir, config_name, "-")

	# save the kernel and map files into test_data_dir
	do_command("cp %s/vmlinux %s/vmlinux.%s" % \
			(build_dir, test_data_dir, config_name))
	do_command("cp %s/System.map %s/System.map.%s" % \
			(build_dir, test_data_dir, config_name))

	# ok, we're done with build
	# re-apply any patches that were popped
	if config_name=="baseline-popped" and have_patches:
		do_command("quilt push -a")

	if not runtime_test:
		print "  No runtime test requested."
		return

	# set localversion for runtime testing
	set_localversion(test_run)

	# build kernel
	rcode, result = do_command_result("ttc %s kbuild" % target)
	if rcode or not os.path.exists("%s/vmlinux" % build_dir):
		failure(test_run, "Could not build %s kernel" % config_name, result)
		return

	# install kernel
	rcode, result = do_command_result("ttc %s kinstall" % target, 1)
	if rcode:
		failure(test_run, "Could not install kernel", result)
		return

	# reset target
	rcode, result = do_command_result("ttc %s reset -w" % target)

	# verify that the running kernel is the one just built
	(kernel_ok, msg) = check_localversion(test_run)
	if not kernel_ok:
		# try a hard reboot, in case reset didn't work
		do_command("ttc %s reboot -w" % target)
		(kernel_ok, msg) = check_localversion(test_run)
		if not kernel_ok:
			failure(test_run, "Kernel just built is not running on board", msg)
			return

	# get used mem on machine
	get_free_mem(test_run)

def do_oldconfig(target):
	do_command('ttc %s setenv -o >env-temp ; source env-temp ; rm env-temp ; yes "" | make oldconfig >/dev/null' % target)

def save_size_data(test_run, kernel_file, config_name, value):
	rcode, result = do_command_result("size %s" % kernel_file)
	if rcode:
		failure(test_run, "Could not get size for kernel")
	else:
		rline = result.split('\n')[1]
		text_size = rline.split()[0]
		data_size = rline.split()[1]
		bss_size = rline.split()[2]
		tot_size = rline.split()[3]
		result_out(test_run, "kernel text size: %s" % text_size)
		result_out(test_run, "kernel data size: %s" % data_size)
		result_out(test_run, "kernel bss size: %s" % bss_size)
		result_out(test_run, "kernel total size: %s" % tot_size)

def clear_localversion(test_run):
	try:
		os.unlink("localversion")
	except:
		pass

def set_localversion(test_run):
	lv_file = open("localversion", "w")
	ver_string = "%06d" % random.randint(0,999999)
	test_run.localversion = ver_string
	print " Setting localversion='%s'" % ver_string
	lv_file.write("-"+ver_string)
	lv_file.close()

def check_localversion(test_run):
	cmd = 'ttc %s run "uname -r"' % test_run.target
	rcode, result = do_command_result(cmd)
	if rcode:
		print "Error collecting results from uname"
		print "result=", result
		# FIXTHIS - need to distinguish board-not-up (this case)
		# from non-matching kernel (below, probably install failure)
		return (0, result)

	print "  On target: kernel release string='%s'" % result
	if result.find(test_run.localversion) == -1: 
		return (0, "expected localversion %s but detected %s" % \
			(test_run.localversion, result))
	else:
		return (1, "")

def get_free_mem(test_run):
	cmd = 'ttc %s run "free -tb"' % test_run.target
	print "  Executing '%s'" % cmd
	(rcode, result) = commands.getstatusoutput(cmd)
	print "result='%s'" % result
	free_mem = "error parsing result='%s'" % result
	if rcode:
		print "Error collecting results from free"
		print "result=", result
		failure(test_run, "Error collecting results from free")
		return 0

	try:
		lines = result.split("\n")
		for line in lines:
			if line.startswith("Total:"):
				free_mem = line.split()[3]
	except:
		pass

	if free_mem.find("error") == -1:
		result_out(test_run, "free memory: %s" % free_mem, result )
		return free_mem
	else:
		failure(test_run, "Error parsing results from free", result)
		return 0

# test an individual option setting 
def test_one_option(test_run, option, value, skip_already_built):
	global runtime_test

	# handle config dependencies here
	deps = None
	if type(value) != type("y"):
		# we have a tuple, break out the option value and the 
		# dependencies
		deps = value[1]
		value = value[0]

	config_name = option[7:]
	test_run.set_id("%s=%s" % (config_name, value))
	print "Running test %s..." % test_run.id

	target = test_run.target
	build_dir = os.environ["KBUILD_OUTPUT"]

	if skip_already_built:
		# check for an already-built option
		opfilename="vmlinux.%s-%s" % (config_name, value)
		if os.path.exists("%s/%s" % (test_data_dir, opfilename)):
			print "%s already exists, skipping..." % opfilename
			return

	# set specific configuration value
	do_command("cp %s/config.baseline %s/.config" % \
			(test_data_dir, build_dir))

	rcode = do_command("ttc %s set_config %s=%s" % (target, option, value))
	if deps:
		for do, dv in deps:
			rcode = do_command("ttc %s set_config CONFIG_%s=%s" % (target, do, dv))

	do_oldconfig(target)

	# save off .config for test script debugging
	rcode = do_command("cp %s/.config %s/config.%s-%s" % (build_dir, test_data_dir, config_name, value))
	
	# verify this config was accepted
	if value=='n':
		option_line = "%s is not set" % option
	else:
		option_line = "%s=%s" % (option, value)
	rcode = do_command('grep "%s" %s/.config' % (option_line, build_dir))
	#print "grep rcode=%d" % rcode
	if rcode:
		failure(test_run, "Could not set configure option %s to value %s" % (option, value))
		return

	cmd = "diff %s/config.baseline %s/config.%s-%s | grep %s >/dev/null" % \
		(test_data_dir, test_data_dir, config_name, value, option)

	print "  Executing '%s'" % cmd
	rcode = os.system(cmd)
	if rcode:
		# no diff found, option is same as in baseline, skip it
		result_out(test_run,
			'Setting matches baseline - skipping build')
		return

	# try diffconfig, if it works, save the result
	cmd = "diffconfig %s/config.baseline %s/config.%s-%s" % \
		(test_data_dir, test_data_dir, config_name, value)
	rcode, result = do_command_result(cmd)
	if not rcode:
		result_out(test_run, "diffconfig result: %s" % result)

	# remove last kernel built, if any
	(rcode) = do_command("rm %s/vmlinux" % build_dir, 0, 1)

	# clear localversion for (possibly?) better ccache-ing
	clear_localversion(test_run)

	# build kernel
	rcode, result = do_command_result("ttc %s kbuild" % target)
	if rcode or not os.path.exists("%s/vmlinux" % build_dir):
		failure(test_run, "Could not build kernel", result)
		return

	# save off kernel and map
	rcode = do_command("cp %s/vmlinux %s/vmlinux.%s-%s" % \
		(build_dir, test_data_dir, config_name, value))
	rcode = do_command("cp %s/System.map %s/System.map.%s-%s" % \
		(build_dir, test_data_dir, config_name, value))

	# get size data for kernel
	save_size_data(test_run, "%s/vmlinux" % build_dir, config_name, value)

	if not runtime_test:
		print "  No runtime test requested."
		return

	# set localversion for runtime testing
	set_localversion(test_run)

	# build kernel
	rcode, result = do_command_result("ttc %s kbuild" % target)
	if rcode or not os.path.exists("%s/vmlinux" % build_dir):
		failure(test_run, "Could not build kernel with localversion", result)
		return

	# install kernel
	rcode = do_command("ttc %s kinstall" % target, 1)
	if rcode:
		failure(test_run, "Could not install kernel")
		return

	# reset target
	rcode, result = do_command_result("ttc %s reset -w" % target)

	# verify that the running kernel is the one just built
	(kernel_ok, msg) = check_localversion(test_run)
	if not kernel_ok:
		# try a hard reboot, in case reset didn't work
		do_command("ttc %s reboot -w" % target)
		(kernel_ok, msg) = check_localversion(test_run)
		if not kernel_ok:
			failure(test_run, "Kernel just built is not running on board", msg)
			return

	# get used mem on machine
	get_free_mem(test_run)


def main():
	global option_list, build_dir, test_data_dir
	global runtime_test

	do_baseline = 1
	do_popped = 0
	do_options = 1
	do_test_options = 0
	do_small = 1
	do_one_shot = 0
	skip_already_built = 0
	runtime_test = 0
	do_wiki_write = 0

	if '-h' in sys.argv:
		usage()
		sys.exit(1)

	if '-V' in sys.argv:
		print "config-size-test.py Version %d.%d.%d" % \
			(MAJOR_VERSION, MINOR_VERSION, REVISION)
		sys.exit(1)

	if '-a-' in sys.argv:
		do_options = 0
		print "Not building configuration alternatives."
		sys.argv.remove("-a-")

	if '-c' in sys.argv:
		skip_already_built = 1
		print "Not building options already built." 
		sys.argv.remove("-c")

	if '-b-' in sys.argv:
		do_baseline = 0 
		print "Not building baseline kernel."
		sys.argv.remove("-b-")

	if '-p' in sys.argv:
		do_popped = 1
		print "Will try to build popped kernel."
		sys.argv.remove("-p")


	if '-s-' in sys.argv:
		do_small = 0
		print "Not building smallest kernel." 
		sys.argv.remove("-s-")

	if '-o' in sys.argv:
		do_one_shot = 1
		one_shot_config = sys.argv[sys.argv.index("-o")+1]
		sys.argv.remove("-o")
		sys.argv.remove(one_shot_config)
		print "Performing one-shot build with config option %s" % \
			one_shot_config

	if '-r' in sys.argv:
		runtime_test = 1
		print "Performing runtime test of free memory"
		sys.argv.remove("-r")

	if '-t' in sys.argv:
		do_test_options = 1
		print "Building the test options, instead of the regular options." 
		sys.argv.remove("-t")


	# check for a remaining arg
	if len(sys.argv)<2:
		print "Error: missing target to run test on."
		usage()
		sys.exit(1)
	else:
		target = sys.argv[1]

	# verify that target is supported by 'ttc'
	(rcode, result) = commands.getstatusoutput('ttc list -q')
	if rcode:
		print "Error: Problem running 'ttc list'"
		sys.exit(1)

	tlist = result.split("\n");
	if target not in tlist:
		print "Error: target '%s' not supported on this host." % target
		print "Available targets are:"
		for t in tlist:
			print "   %s" % t
		print
		usage()
		sys.exit(1)

	test_run = test_run_class(test_suite_name, target)
	test_data_dir = test_data_dir_top + "-" + target

	# make directory for test output
	# (remove leading ../ from test_data_dir, since we haven't
	# changed to the kernel source dir yet.)
	do_command("install -d %s" % test_data_dir[3:], 1)

	# log results
	test_run.start_log(test_data_dir[3:])

	# Here is the actual testing
	print "Running tests on target: %s" % target

	test_setup(test_run)

	if do_baseline:
		test_kernel(test_run, "baseline")

	if do_popped:
		test_kernel(test_run, "baseline-popped")

	if do_one_shot:
		# parse one_shot_config
		if one_shot_config.find('=')==-1:
			one_shot_option = one_shot_config
			values = ('y|n')
		else:
			(one_shot_option, values) = one_shot_config.split('=')
		one_shot_values = values.split('|')

		option_list = [(one_shot_option, one_shot_values)]

		# override silly people who specify an option to test, but
		# turn off do_options.
		do_options = 1
	else:
		# add yes_no options to default options list
		# put yes/no options at front of list
		for option in yes_no_options:
			option_list.insert(0, (option, ('y','n')))

	# now test each option
	if do_options:
		# set to the alternate list, if requested
		if do_test_options:
			option_list = test_list

		total_options = len(option_list)
		cur_option = 1
		for (option, values) in option_list:
			print "Now on option %d, out of %d (time=%s)" % \
				(cur_option, total_options, time.localtime())
			option = "CONFIG_"+option
			for value in values:
				test_one_option(test_run, option, value,
					skip_already_built)
			cur_option += 1

	# now try to build the smallest kernel possible
	if do_small:
		test_kernel(test_run, "smallest")

	# close the log results
	test_run.close_log()

	# show a results summary
	print "\n###########################################"
	print "Results summary:"
	test_run.show_summary_results()

main()
