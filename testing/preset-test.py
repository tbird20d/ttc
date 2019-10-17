#!/usr/bin/python
#
# preset-test.py - python routine to test preset LPJ
#
# To Do for preset-test.py
# * don't hardcode calibration success threshhold (currently 2 milliseconds)
# * do better handling of regular expression mismatch (missing group)
#   * currently, the test exits with an exception. (see below)
#
# To Do for test framework:
# * allow sub-command output to pass through if "-v" is specified
# * create vprint routine to print status lines only in verbose mode
# * auto-detect if manual_reset is needed
# * ring a bell when manual_reset is needed
# * make a convenience routine to perform "ttc" commands
# * create table of summary results at end of test
#   * support text, wiki or html output format for table
#
#
# BUGS:
#  * failure of telnet_exec (ttc run) is not handled properly:
#
# here's a dump:

MAJOR_VERSION = 0
MINOR_VERSION = 9
REVISION      = 1

#Sleeping 30 seconds to wait for board to reset
#Executing 'ttc ebony run "dmesg | grep Calib ; dmesg | grep Mount-cache"'
#Error collecting results from dmesg
#result= Traceback (most recent call last):
#  File "/home/tbird/bin/telnet_exec", line 83, in ?
#    result = tn.read_until("login: ")
#  File "/usr/lib/python2.3/telnetlib.py", line 324, in read_until
#    return self.read_very_lazy()
#  File "/usr/lib/python2.3/telnetlib.py", line 400, in read_very_lazy
#    raise EOFError, 'telnet connection closed'
#EOFError: telnet connection closed
#Error: Bad result 256, running "telnet_exec -t ebony -u root -c "$COMMAND"": (output follows)
#Error:
#cmd= telnet_exec -t ebony -u root -c "$COMMAND"
#result=
#result=
#Traceback (most recent call last):
#  File "/home/tbird/bin/telnet_exec", line 83, in ?
#    result = tn.read_until("login: ")
#  File "/usr/lib/python2.3/telnetlib.py", line 324, in read_until
#    return self.read_very_lazy()
#  File "/usr/lib/python2.3/telnetlib.py", line 400, in read_very_lazy
#    raise EOFError, 'telnet connection closed'
#EOFError: telnet connection closed
#Error: Bad result 256, running "telnet_exec -t ebony -u root -c "$COMMAND"": (output follows)
#Error:
#cmd= telnet_exec -t ebony -u root -c "$COMMAND"
#result=
#Traceback (most recent call last):
#  File "/home/tbird/work/auto-preset-test/preset-test.py", line 135, in ?
#    bogomips1 = m.group(1)
#AttributeError: 'NoneType' object has no attribute 'group'

import os, sys
import commands
import re
import time

######################################
# Define some globals for this test suite

test_suite_name="PRESET_LPJ"
src_dir = "test-linux"
test_data_dir = "../test-data"

# FIXTHIS - following attributes should be detected automatically (per board)?
# (use 'ttc info -n <attribute>' ???)

# indicate if target board needs manual reset
# board reset must be one of: "manual", "console reboot", and "hardware"
# uncomment the appropriate line for the board
# FIXTHIS - should detect this from 'ttc info -n reset_type'
#board_reset = "manual"
#board_reset = "console reboot"
board_reset = "hardware"
# number of seconds to wait for board to reset
reset_sleep = 60

######################################
# Define some convience classes and functions

def usage():
	print """Usage: %s [-h] <target>

where <target> is the name of the target to be used with
the 'ttc' command.

-h	show this usage help
-V	show version information
""" % os.path.basename(sys.argv[0])

class test_run_class:
	def __init__(self, suite_name, target):
		self.suite_name = suite_name
		self.target = target
		self.set_id('001')
		self.results_list = []

	def set_id(self, id):
		self.id = self.suite_name+"-"+id

	def show_results(self, format='text'):
		for (rtype, result, extra_data) in self.results_list:
			# FIXTHIS - rtype is just thrown away right now
			# FIXTHIS - should vary output depending on format arg
			print result

# maybe these should be test_run_class methods???
# (but it makes actual test code more verbose)
def result_out(test_run, msg, extra_data=''):
	out_msg = "[TEST: %s] Result - %s" % (test_run.id, msg)
	print out_msg
	test_run.results_list.append(("result", out_msg, extra_data))

def success(test_run, msg, extra_data=''):
	out_msg = "[TEST: %s] Success - %s" % (test_run.id, msg)
	print out_msg
	test_run.results_list.append(("success", out_msg, extra_data))

def failure(test_run, msg, extra_data=''):
	out_msg = "[TEST: %s] Failure - %s" % (test_run.id, msg)
	print out_msg
	test_run.results_list.append(("failure", out_msg, extra_data))

def do_command(cmd, exception_on_error=0):
	print "  Executing '%s'" % cmd
	(rcode, result) = commands.getstatusoutput(cmd)
	if rcode:
		err_str = 'Error running cmd "%s"' % cmd
		print err_str
		print 'command output=%s' % result
		if exception_on_error:
			raise ValueError, err_str
	return rcode

# unused right now - may use later to get value for manual_reset
def get_target_value(target, var_name):
	cmd = "ttc %s info -n %s" % (target, var_name)
	(rcode, result) = commands.getstatusoutput(cmd)
	if rcode:
		err_str = 'Error running cmd "%s"' % cmd
		raise ValueError, err_str
	value = result
	return value

def reset_target(target, reset_type):
	# perform the operation, supported by the target, for restarting the board
	if reset_type == "hardware":
		rcode = do_command("ttc %s reset" % target)
	elif reset_type == "console reboot":
		rcode = do_command("ttc %s run reboot" % target)
	elif reset_type == "manual":
		print "*** Manual reset required - please reset the board and hit <enter>"
		sys.stdin.readline()
	else:
		print "Unsupported board_reset value - %s" % reset_type

	# wait a bit
	print "Sleeping %d seconds to wait for board to reset" % reset_sleep
	time.sleep(reset_sleep)

def set_localversion(test_run):
	lv_file = open("localversion", "w")
	lv_file.write("-"+test_run.id+"\n")
	lv_file.close()

def check_localversion(test_run):
	cmd = 'ttc %s run "uname -r"' % test_run.target
	(rcode, result) = commands.getstatusoutput(cmd)
	if rcode:
		print "Error collecting results from uname"
		print "result=", result
	print "result='%s'" % result
	localversion = result.split("-")[-1]
	print "kernel localversion=",localversion
	if localversion==test_run.id:
		return 1
	else:
		return 0
	

def test_setup(tr):
	# 'tr' stands for 'test run'

	# test run prep
	# 1. get kernel
	# 2. get default config
	print "Doing test preparation for %s tests..." % tr.suite_name

	# auto-detect that kernel is already present in src_dir
	# and skip the get_kernel automatically
	rcode = do_command('test -f %s/gk_marker' % src_dir)
	if rcode:
		do_command("ttc %s get_kernel -o %s" % (tr.target, src_dir), 1)
		do_command('echo "get_kernel completed" >%s/gk_marker' % src_dir)
	else:
		print "*** Skipping get_kernel (get_kernel marker found)"

	os.chdir(src_dir)

	build_dir = "../test-build/%s" % tr.target
	os.environ["KBUILD_OUTPUT"]=build_dir

	rcode = do_command("install -d %s" % build_dir, 1)

	rcode = do_command("ttc %s get_config" % tr.target, 1)

#############################################
# PRESET_LPJ-001
def test_001(tr):
	global lpj, bogomips1

	tr.set_id("001")
	print "Running test %s..." % tr.id

	# 3. set specific configuration values
	#    * PRINTK_TIMES
	#    * fast boot options
	#    * PRESET_LPJ=0
	#    * quiet

	rcode = do_command("ttc %s set_config CONFIG_PRINTK_TIME=y" % tr.target, 1)
	rcode = do_command("ttc %s set_config CONFIG_FASTBOOT=y" % tr.target, 1)
	rcode = do_command("ttc %s set_config CONFIG_PRESET_LPJ=0" % tr.target, 1)
	rcode = do_command("ttc %s set_config CONFIG_LOG_BUF_SHIFT=17" % tr.target, 1)
	rcode = do_command('ttc %s set_config "CONFIG_CMDLINE+=\\" quiet\\""' % tr.target, 1)

	# FIXTHIS - verify these configs were accepted

	set_localversion(tr)

	# 4. build kernel
	rcode = do_command("ttc %s kbuild" % tr.target)
	#print "*** Skipping kbuild"
	if rcode:
		failure(tr, "Could not build kernel")

	# FIXTHIS - verify that the kernel built OK

	# 5. install kernel
	if not rcode:
		rcode = do_command("ttc %s kinstall" % tr.target, 1)
		if rcode:
			failure(tr, "Could not install kernel")

	# 6. reset target
	if not rcode:
		reset_target(tr.target, board_reset)

	# verify that the running kernel is the one just built
	check_localversion(tr)

	# 7. run dmesg
	#    * gather data from 'Calibrating' line
	if not rcode:
		cmd = 'ttc %s run "dmesg -s 64000 | grep Calib ; dmesg -s 64000 | grep Mount-cache"' % tr.target
		print "  Executing '%s'" % cmd
		(rcode, result) = commands.getstatusoutput(cmd)
		if rcode:
			print "Error collecting results from dmesg"
			print "result=", result

		print "result=\n", result
		lines = result.split('\n')

		# read BogoMIPS
		pat = ".* ([.0-9]+) BogoMIPS"
		m = re.match(pat, lines[0])
		bogomips1 = m.group(1)
		print "bogomips1=%s" % bogomips1

		# read lpj
		pat = ".*lpj=([0-9]*)\)"
		m = re.match(pat, lines[0])
		lpj = m.group(1)
		print "lpj=%s" % lpj
			
	# 8. determine timing with PRESET_LPJ off
		pat = "\[([ .0-9]*)\].*"
		m = re.match(pat, lines[0])
		time1 = float(m.group(1))
		m = re.match(pat, lines[1])
		time2 = float(m.group(1))
		delta1 = time2 - time1
		print "delta1=", delta1
		result_out(tr, "Calibration took %f seconds with preset LPJ off\n" % delta1)

#############################################
# PRESET_LPJ-002
def test_002(tr):
	global lpj, bogomips1

	tr.set_id("002")
	print "Running test %s..." % tr.id

	# 3. set specific configuration values
	#   * CONFIG_CMDLINE+=" lpj=<value>"
	rcode = do_command('ttc %s set_config "CONFIG_CMDLINE+=\\" lpj=%s\\""' % (tr.target, lpj), 1)

	# 4. build kernel
	rcode = do_command("ttc %s kbuild" % tr.target)
	#print "*** Skipping kbuild"
	if rcode:
		failure(tr, "Could not build kernel")

	# 5. install kernel
	if not rcode:
		rcode = do_command("ttc %s kinstall" % tr.target, 1)
		if rcode:
			failure(tr, "Could not install kernel")

	# 6. reset target
	if not rcode:
		reset_target(tr.target, board_reset)

	# 7. run dmesg
	#    * gather data from 'Calibrating' line
	if not rcode:
		cmd = 'ttc %s run "dmesg -s 64000 | grep Calib ; dmesg -s 64000 | grep Mount-cache"' % tr.target
		print "  Executing '%s'" % cmd
		(rcode, result) = commands.getstatusoutput(cmd)
		if rcode:
			print "Error collecting results from dmesg"
			print "result=", result

		print "result=\n", result
		lines = result.split('\n')

		# read BogoMIPS
		pat = ".* ([.0-9]*) BogoMIPS"
		m = re.match(pat, lines[0])
		try:
			bogomips2 = m.group(1)
			print "bogomips2=%s" % bogomips2
		except:
			print "Couldn't read BogoMIPS from dmesg output"
			print "dmesg output was:\n", result

		# value for BogoMIPS should match non-preset case
		if bogomips1==bogomips2:
			success(tr, "BogoMIPS value is the same with preset lpj")
		else:
			failure(tr, "BogoMIPS value was changed with preset lpj")
			print "dmesg output was:\n", result

		pat = ".*skipped.*preset"
		m = re.match(pat, lines[0])
		if m:
			success(tr, "lpj value was preset.")
		else:
			failure(tr, "lpj value was not preset")
			print "dmesg output was:\n", result
			
	# 8. determine timing with PRESET_LPJ specified on
		pat = "\[([ .0-9]*)\].*"
		m = re.match(pat, lines[0])
		time1 = float(m.group(1))
		m = re.match(pat, lines[1])
		time2 = float(m.group(1))
		delta2 = time2 - time1
		print "delta2=", delta2
		result_out(tr, "Calibration took %f seconds with preset LPJ on kernel command line\n" % delta2)

		# test result - delta2 should be small (less than 2 milliseconds)
		if delta2 < 0.002:
			success(tr, "calibration took less than 2 milliseconds")
		else:
			failure(tr, "calibration took longer than 2 milliseconds.")


#############################################
# PRESET_LPJ-003
def test_003(tr):
	global lpj, bogomips1

	tr.set_id("003")
	print "Running test %s..." % tr.id

	# 3. reset config, and then set specific configuration values
	#    * PRINTK_TIMES
	#    * fast boot options
	#    * PRESET_LPJ=<value>
	#    * quiet
	rcode = do_command("ttc %s get_config" % tr.target, 1)


	rcode = do_command("ttc %s set_config CONFIG_PRINTK_TIME=y" % tr.target, 1)
	rcode = do_command("ttc %s set_config CONFIG_FASTBOOT=y" % tr.target, 1)
	rcode = do_command("ttc %s set_config CONFIG_LOG_BUF_SHIFT=17" % tr.target, 1)
	rcode = do_command('ttc %s set_config "CONFIG_CMDLINE+=\\" quiet\\""' % tr.target, 1)
	rcode = do_command("ttc %s set_config CONFIG_PRESET_LPJ=%s" % (tr.target, lpj), 1)

	# 4. build kernel
	rcode = do_command("ttc %s kbuild" % tr.target)
	#print "*** Skipping kbuild"
	if rcode:
		failure(tr, "Could not build kernel")

	# 5. install kernel
	if not rcode:
		rcode = do_command("ttc %s kinstall" % tr.target, 1)
		if rcode:
			failure(tr, "Could not install kernel")

	# 6. reset target
	if not rcode:
		reset_target(tr.target, board_reset)

	# 7. run dmesg
	#    * gather data from 'Calibrating' line
	if not rcode:
		cmd = 'ttc %s run "dmesg -s 64000 | grep Calib ; dmesg -s 64000 | grep Mount-cache"' % tr.target
		(rcode, result) = commands.getstatusoutput(cmd)
		if rcode:
			print "Error collecting results from dmesg"
			print "result=", result

		print "result=\n", result
		lines = result.split('\n')

		# read BogoMIPS
		pat = ".* ([.0-9]*) BogoMIPS"
		m = re.match(pat, lines[0])
		try:
			bogomips3 = m.group(1)
			print "bogomips3=%s" % bogomips3
		except:
			print "Couldn't read BogoMIPS from dmesg output"
			print "dmesg output was:\n", result

		# value for BogoMIPS should match non-preset case
		if bogomips1==bogomips3:
			success(tr, "BogoMIPS value is the same with static preset lpj")
		else:
			failure(tr, "BogoMIPS value was changed with static preset lpj")
			print "dmesg output was:\n", result

		pat = ".*skipped.*preset"
		m = re.match(pat, lines[0])
		if m:
			success(tr, "lpj value was preset.")
		else:
			failure(tr, "lpj value was not preset")
			print "dmesg output was:\n", result
			
	# 8. determine timing with PRESET_LPJ compiled statically in the kernel
		pat = "\[([ .0-9]*)\].*"
		m = re.match(pat, lines[0])
		time1 = float(m.group(1))
		m = re.match(pat, lines[1])
		time3 = float(m.group(1))
		delta3 = time3 - time1
		print "delta3=", delta3
		result_out(tr, "Calibration took %f seconds with preset LPJ compiled into kernel\n" % delta3)

		# test result - delta3 should be small (less than 2 milliseconds)
		if delta3 < 0.002:
			success(tr, "calibration took less than 2 milliseconds")
		else:
			failure(tr, "calibration took longer than 2 milliseconds.")

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
		print "preset-test.py Version %d.%d.%d" % (MAJOR_VERSION, MINOR_VERSION, REVISION)
		sys.exit(1)

	target = sys.argv[1]

	if target not in tlist:
		print "Error: target '%s' not supported on this host." % target
		print "Available targets are:"
		for t in tlist:
			print "   %s" % t
		print
		usage()
		sys.exit(1)

	#################################################
	# Here is the actual testing
	test_run = test_run_class(test_suite_name, target)

	print "Running tests on target: %s" % target
	test_setup(test_run)
	test_001(test_run)
	test_002(test_run)
	test_003(test_run)

	print "\n###########################################"
	print "Results summary:"
	test_run.show_results()

if __name__=="__main__":
	main()
