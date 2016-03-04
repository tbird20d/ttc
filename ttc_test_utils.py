#!/usr/bin/python
#
# ttc_test_utils.py - module with test utilities for use with lab set up 'ttc'
#
# To Do for test utils:
# * allow sub-command output to pass through to stdout if "-v" is specified
# * create vprint routine to print status lines only in verbose mode
# * create table of summary results at end of test
#   * support text, wiki or html output format for table
#
# BUGS:
#  * failure of telnet_exec (ttc run) is not handled properly:
#
MAJOR_VERSION = 0
MINOR_VERSION = 4
REVISION      = 0

import os, sys
import commands
import re
import time
import random

reset_timeout_default = 60

def get_timestamp():
	t = time.time()
	tfrac = int((t-int(t))*10000)
	timestamp = time.strftime("%Y-%m-%d_%H:%M:%S.")+("%04d" % tfrac)
	return timestamp

class test_run_class:
	def __init__(self, suite_name, target):
		self.suite_name = suite_name
		self.target = target
		self.run_uid = "%04d" % random.randint(1,10000)

		# results_list is a list of triples, with 
		# (<event_type>, <msg>, <extra_data>)
		self.results_list = []
		self.id = '000'
		self.time = time.localtime()
		self.logfd = None

		try:
			rcode, result = self.do_command_result("hostname", 1)
			self.hostname = result.strip()
		except:
			self.hostname="unknown_host"

	def set_id(self, id, desc):
		self.id = self.suite_name+"-"+id
		timestamp = get_timestamp()
		new_msg = "[TEST: %s - %s] Starting at %s" % (self.id, desc, timestamp)
		self.print_and_log_message(new_msg)

	def print_and_log_message(self, msg, extra_data=''):
		print msg
		sys.stdout.flush()

		if self.logfd:
			self.logfd.write(msg+"\n")
			if extra_data:
				self.logfd.write(extra_data+"\n")
			self.logfd.flush()
		

	def save_result_str(self, rtype, msg, extra_data):
		self.results_list.append((self.id, rtype, msg, extra_data))
		out_msg = "[TEST: %s] %s - %s" % (self.id, rtype, msg)
		self.print_and_log_message(out_msg, extra_data)

	def start_log(self, test_data_dir):
		t = time.strftime("%Y.%m.%d-%H:%M:%S", self.time)
		logfilename = test_data_dir + "/%s-%s-%s-%s.log" % \
			(self.suite_name, self.target, t, self.run_uid)
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

	def result_out(self, msg, extra_data=''):
		self.save_result_str("RESULT", msg, extra_data)

	def success(self, msg, extra_data=''):
		self.save_result_str("SUCCESS", msg, extra_data)

	def failure(self, msg, extra_data=''):
		self.save_result_str("FAILURE", msg, extra_data)

	def do_command(self, cmd, exception_on_error=0, ignore_error=0):
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

	def do_command_result(self, cmd, exception_on_error=0, ignore_error=0):
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

	def do_ttc(self, cmd, exception_on_error=0):
		ttc_cmd = "ttc %s %s" % (self.target, cmd)
		return self.do_command(ttc_cmd)

	def run_on_target(self, cmd, exception_on_error=0):
		run_cmd = 'ttc %s run "%s"' % (self.target, cmd)
		return self.do_command_result(run_cmd)

	def check_config(self, config, value):
		# VALUE Should be one of y,n or a numeric value 
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

	def do_make_oldconfig(self):
		# make a best effort attempt to run oldconfig with
		# appropriate target settings.
		# stupid MIPS doesn't take CROSS_COMPILE from environment!!
		arch = self.get_target_value("ARCH", "")
		cross_compile = self.get_target_value("CROSS_COMPILE", "")

		status = os.system("""ttc %s setenv -o >temp_ttc_env ; source ./temp_ttc_env ; rm temp_ttc_env ; yes "" | make ARCH=%s CROSS_COMPILE=%s oldconfig >oc_result""" % (self.target, arch, cross_compile))

		result = open("oc_result").read()
		os.remove("oc_result")
		return (status, result)

	def get_target_value(self, var_name, default_value):
		cmd = "ttc %s info -n %s" % (self.target, var_name)
		(rcode, result) = commands.getstatusoutput(cmd)
		if rcode:
			value = default_value
		else:
			value = result
		return value

	def reset_target(self, reset_type):
		# perform specified operation for restarting the board
		if reset_type == "reset":
			rcode = self.do_ttc("reset -w")
		elif reset_type == "console reboot":
			rcode = self.do_ttc("run reboot")
		elif reset_type == "reboot":
			rcode = self.do_ttc("reboot")
		elif reset_type == "manual":
			print "*** Manual reset required - please reset the board and hit <enter>"
			sys.stdin.readline()
		else:
			print "Unsupported board_reset value - %s" % reset_type

		# wait a bit
		reset_timeout = int(self.get_target_value("reset_timeout", reset_timeout_default))
		print "  Sleeping %d seconds to wait for board to reset" % reset_timeout
		time.sleep(reset_timeout)

	def wait_for_target_to_boot(self, max_wait_time=60):
		# max_wait_time is in seconds
		# returns 0 on success, or 1 on failure
		t1 = time.time()
		t2 = time.time()
		rcode = 2
		while (rcode != 0 and t2-t1<max_wait_time):
			(rcode, result) = self.run_on_target("echo hello")
			print "rcode in wait_for_target_to_boot = %d" % rcode
			print "time remaining =", max_wait_time - (t2-t1)
			t2 = time.time()
			# wait at least some time before re-trying
			if rcode != 0:
				time.sleep(1)
		return rcode

	def clear_localversion(self):
		try:
			os.unlink("localversion")
		except:
			pass

	def set_localversion(self, id_str=None):
		if not id_str:
			id_str = 'ID'+("%04d" % random.randint(1,10000))
		print "  Setting localversion to '%s'" % id_str
		lv_file = open("localversion", "w")
		lv_file.write("-"+id_str+"\n")
		lv_file.close()
		self.kernel_id = id_str

	def check_localversion(self, id_str=None):
		if not id_str:
			id_str = self.kernel_id
		(rcode, result) = self.run_on_target("uname -r")
		if rcode:
			self.failure("Error collecting results from 'uname -r'", result)
			print "result=", result
			return 0
		result_list = result.split("\n")

		# FIXTHIS - this is a kludge to work around some sub-program returning
		# too much output
		if result_list[0].startswith("cmd="):
			result = result_list[1]
		else:
			result = result_list[0]

		print "Version of running kernel is: '%s'" % result
		print "id_str='%s'" % id_str
		if result.find(id_str) != -1:
			return 1
		else:
			return 0

