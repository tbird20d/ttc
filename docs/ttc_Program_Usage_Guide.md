Overview
========

This document describes the program `ttc`, which is a tool
for developing Linux for embedded systems.

`ttc` is intended to be used in a host/target development
configuration, where one machine is the development host where software
is configured and built, and one or more machines are targets where
software is executed.  This is the most common configuration for
embedded systems programming.  The <code>ttc</code> program is run on
the host system in order to build software and interact with target
machines in a common way.

The <code>ttc</code> program can be run interactively, or as part of an
automated session.  The purpose of <code>ttc</code> is to make it so
that the same commands can be used to build software and manipulate
different target machines, independent of differences in the
configuration and setup of the machines.  Certain details of operation
are hidden from the user by the <code>ttc</code> command.  This makes it
possible to perform the same operations on different target boards,
using the same set of <code>ttc</code> commands.

When the <code>ttc</code> program runs, it reads the configuration file
"<code>/etc/ttc.conf</code>".  Usually, it looks up the target to act
upon (which is specified either on the command line or in the
environment), then sets up the environment for the desired sub-command.
(The set of supported sub-commands is listed below in the section
"Commands".) Finally, using the attributes specified in the
configuration file, <code>ttc</code> executes the specified sub-command.

The different operations (or sub-commands) of <code>ttc</code> are
intended to support the following major development activities related
to a target:
* retrieving kernel source
* patching the kernel
* configuring the kernel for the target, including both:
:* getting a default configuration for the target
:* modifying individual configuration options
* building the kernel
* installing the kernel on the target
* rebooting the target machine
* accessing the console for the target
* copying files to and from the target

Note that there is NOT a one-to-one correspondence between the
<code>ttc</code> sub-commands and the activities listed above.  This is
because once the environment is set up it is possible to perform some of
these activities in a target-independent way using normal Linux commands
(like "make" or "patch").

In reality, <code>ttc</code> is a rather thin wrapper program which sets
up the environment and performs some common operations.  The bulk of the
"intelligence" (how to do the actual operations) is contained in the
configuration file in the form of Unix shell commands.

In order to use <code>ttc</code> on your system, you need to install the
software and edit the configuration file to match your host/target
setup.  You may also need to install various helper scripts, referenced
in your ttc.conf file, in your PATH.
  
Theory of operation
===================

The most important aspect of <code>ttc</code> is that it hides certain
operational details from the user, so that common commands can be used
to perform operations related to an embedded development board.

The things that <code>ttc</code> hides, include things such as:
* the location and name of the cross-compiler (and other toolchain programs)
* the version and location of the Linux kernel source code
* the menu location of kernel configuration options
* the method of installing the kernel on the target board
* the method of rebooting the target board
* the method of installing files to the file system of the target

These things must be set up on the host machine, and then the
<code>ttc</code> configuration file must be written to take into account
the specific settings for each target connected to the host.

Downloading 'ttc'
-----------------

Download the tarball from one of the following links and follow the
instructions in the README (and in this document).

{| border="1" cellpadding="5" cellspacing="0"
!style="background:#80cccc;"|'''Version'''
!style="background:#80cccc;"|'''Description'''
!style="background:#80cccc;"|'''Download Link'''
|-
|''current''||Public release as of March 4, 2016||https://github.com/tbird20d/ttc
|-
|1.3.0||Public release as of January 13, 2014||[[Media:Ttc-1.3.0.tgz | Ttc-1.3.0.tgz]]
|-
|1.2.3||Public release as of Dec 12, 2012||[[Media:Ttc-1.2.3.tgz | Ttc-1.2.3.tgz]]
|}

Installing 'ttc'
----------------

Copy <code>ttc</code> to <code>/usr/local/bin</code>.  If you want to
use any of the provided helper scripts on your system (ssh_exec,
telnet_exec, powerswitch-cycle), you should put them somewhere on your
search PATH.  <code>/usr/local/bin</code> would be a good place to copy
them to.

Configuring 'ttc'
-----------------

In order to use 'ttc', you first need to set up the
<code>/etc/ttc.conf</code> configuration file for the targets attached
to your host machine.  This is usually a relatively easy thing to do,
but may require special hardware or software to provide the services
that 'ttc' needs to access the board.

The syntax of the configuration file, and a description of the required
contents, is in Appendix A.  Also, a sample configuration file is
provided, with definitions for several targets.

See the section "Configuration files and environment variables" for
additional notes on where to place configuration information.

Note that not all variables need to be defined for a target, in order
for a target configuration to be useful.  For example, if you never
re-build the distribution for a target, you do not need to configure the
fsbuild or fsinstall commands.  In general, you should start with a
minimal configuration which meets your needs, and then expand to
configuring additional features as you use those features on the board.

Using 'ttc'
-----------

You can use 'ttc' interactively from the Linux command line, or you can
use it by running an automated test (which invokes target to perform
various parts of the test.)

Commands
========

Command Overview
----------------

Here is the list of sub-commands available for user with the
<code>ttc</code> command.

| Command   | Operation                                               | Notes |
| --------- | ------------------------------------------------------- | ----- |
| console   | Run a program to access the target console.             | foo   |
| cp        | Copy files to or from the target.                       |
| fsbuild   | File system build                                       |
| fsinstall | File system install                                     |
| get_config| Install kernel config in the $KBUILD_OUTPUT directory   | assumes the current directory is top kernel source dir.
| get_kernel| Install kernel source in the $KERNEL_SRC directory      |
| help      | Show this online help.                                  |
| info      | Show information about a target.                               |
| kbuild    | Build kernel from source.                                      | assumes the current directory is the top kernel source dir.
| kinstall  | Install kernel for use on target.                              | assumes the current directory is the top kernel source dir.
| list      | Show a list of available targets.                              |
| login     | Run a program to perform a network login on the target.        |
| off       | Turn target off                                                |
| on        | Turn target on                                                 |
| pos       | Show power status of target                                    |
| reboot    | Reboot (power on and off) target board.                        |
| release   | Release a reservation of a target.                             |
| reserve   | Reserve a target for use.                                      |
| reset     | Reset target board.                                            |
| rm        | Remove files from the target.                                  |
| run       | Run a command on the target, collecting it's output            |
| set_config | Set an individual config option                               | assumes the current directory is top kernel source dir
| setenv    | Starts shell with environment for performing build and other operations |
| status    | Show status of target, including reservations.                 | not implemented yet (currently only shows reservation, but not board status)
| vars      | Show information about environment vars used by 'ttc'          |
| version   | Show version information and exit.                             |
| wait_for  | Wait for a condition to be true.                               | command is executed on host (not on the target)

Use cases
~~~~~~~~~

Example 1: build and install a kernel, and logon to the target to use it
````````````````````````````````````````````````````````````````````````
A normal sequence of operations for an interactive user of <code>ttc</code> would be:

* get a list of targets connected to this host
* select a target to work on, and set up the environment for it
* get the kernel sources for a build
* (optionally) apply patches to the kernel sources
* get a (default) kernel configuration for this target
* set specific configuration options
* build the kernel, and install it
* reboot the target with the new kernel
* (optionally) put additional files on the target
* access the target console and do work

------
Here are the <code>ttc</code> commands one would use to accomplish this:

*  get a list of targets connected to this host
<pre>$ ttc list
Targets on this host:
    ebony
    innovator
    nut
    osk
    test
</pre>

* select a target to work on, and set up environment for it

<pre>
$ ttc ebony setenv
</pre>

* get the kernel sources for a build

<pre>
$ ttc get_kernel -o linux-test
$ cd linux-test
</pre>

* (optionally) apply patches to the kernel sources
<pre>
$ patch -p1 <../printk-times.patch
</pre>

* get a default kernel configuration for this target
<pre>
$ ttc get_config
</pre>

* set specific configuration options

<pre>
$ ttc set_config CONFIG_PRINTK_TIME==y
</pre>

* build the kernel, and install it

<pre>
$ ttc kbuild
$ ttc kinstall
</pre>

* reboot the target with the new kernel
(either one of: On the target board, type "reboot":

<pre>
$ reboot
</pre>
or from the host, use:

<pre>
$ ttc reset
</pre>

* (optionally) put additional files on the target
<pre>
$ ttc cp foo bar target:/tmp
$ ttc cp test.sh target_bin:
</pre>

* login to the console and do some work

<pre>
$ ttc console
<do interactive work on the target>
</pre>

==== Commands ====
===== console =====
Runs a program to access the target console.

Usage: ttc [<target>] console

A program is run to provide interactive access to the target
console.  It is not possible to predict what program will be
used. Often it is <code>minicom</code>, talking to a serial console
on the target. But the access program could be something else,
so no assumptions should be made.  This command is not intended
to support automated access to the target console.  Use
'ttc run' for that.

===== cp =====
Copy files to or from the target.

Usage: ttc [<target>] cp <src1> [<src2> ...] <dest>

The last path specified determines the direction of the copy.
Use the prefix "target:" to specify a filepath
on the target.  "target_bin:" can be used to put a file on the target
in a directory on the PATH.

* Ex: ttc cp test_data test_data2 target:/tmp
* Ex: ttc cp test.sh target_bin:

===== get_config =====
Install kernel config for target in the $KBUILD_OUTPUT directory

Usage: ttc [<target>] get_config [-o <otherdir>]

Use -o to specify an alternate KBUILD_OUTPUT directory (default is '.')
Assumes the current directory is the top kernel source dir.

===== get_kernel =====
Install kernel sources for target in the $KERNEL_SRC directory

Usage: ttc [<target>] get_kernel [-o <outputdir>]

Use -o to specify a specific output kernel source directory.
The default output directory, if none is specified, is 'linux'.

===== help =====
Show the online help.

Usage: ttc help [<command>]

If a command is specified, show help Release a reservation of a target.and usage information for that command.

===== info =====
Show information about a target.

Usage ttc [<target>] info [-v] [-n <attr>]

Show information about a target.  The '-v' (verbose) option will show all the
attributes for the target (from the configuration file).  Use the '-n' option
to display the value of a single attribute, <attr>.

===== kinstall =====
Install kernel for use on target.

Usage: ttc [<target>] kinstall

Assumes the current directory is the top kernel source directory.

===== list =====
Show a list of available targets.

Usage: ttc list [-q]

Use -q for "quiet" mode.  This suppresses extraneous output.  The resulting
list can be parsed more easily by other programs.

===== login =====
Run a program to perform a network login on the target.

Usage: ttc [<target>] login

===== on =====
Turn on the power to the target

Usage: ttc [<target>] on

===== off =====
Turn off the power to the target

Usage: ttc [<target>] off

===== pos =====
Show the power status of the target

Usage: ttc [<target>] pos

===== reboot =====
Reboot the target board.

Usage: ttc [<target>] reboot [-w]

This performs a reboot (power cycle) of the target board. Use the '-w' option to have ttc wait a period 
of time before returning, to allow the board to reset.  The length of the wait is determined by the 'reset_delay'
specified for the board.

===== reset =====
Reset the target board.

Usage: ttc [<target>] reset [-w]

This performs a soft reset of the target board, if available.  Note that if the hardware configuration
does not support a soft reset, a reboot may be performed instead.  Use the '-w' option to have ttc wait a period 
of time before returning, to allow the board to reset. The length of the wait is determined by the 'reset_delay'
specified for the board.

===== rm =====
Remove files from the target.

Usage: ttc [<target>] rm <file1> [<file2>...]

===== run =====
Run a command on the target, and return it's output.

Usage: ttc [<target>] run "command <args>"

===== set_config =====
Set one or more individual config options

Usage: ttc [<target>] set_config [-o <outputdir>] <option-def> ...

Use -o to specify a non-default KBUILD_OUTPUT directory. (The default is '.'
if none is specified in the environment or the target.conf file.)

Multiple <option-defs> may be specified with one command.  Each
<option-def> has the syntax: <option-name><operation><value>.i
Operations are: '=' for assignment, and '+=' for a string append.
Boolean or tristate values should be one of "y", "n", and "n".
String values must be enclosed in quotes, which usually requires shell
escaping of the quote characters (see below).

A backup is made of the .config file.

Examples:
* ttc set_config CONFIG_FOO=y
* ttc set_config CONFIG_BAR=n CONFIG_BAZ=1234
* ttc set_config "CONFIG_STR=\"foo bar\""
* ttc set_config "CONFIG_STR+=\" quiet\""


Assumes the current directory is the top kernel source dir.

===== setenv =====
Prepare environment for building for the target

Usage: ttc [<target>] setenv [-o >file]

This command starts a new shell, with an environment that is 
prepared for building for the target.  That is, things like
KBUILD_OUTPUT, CROSS_COMPILE, and ARCH are set in the environment,
and PATH has been adjusted to include the appropriate toolchain
directory.

When -o is used, no new sub-shell is started.  Rather, 
-o causes target to output the required environment variables
as a series of shell export statements.  These can be
'sourced' into the current shell rather than starting a new
sub-shell.

* Ex: ttc ebony setenv -o >foo ; source foo

===== status =====
Show status of target, including reservations.

Usage: ttc [<target>] status

This command shows the the status of the indicated target.
The full command for showing status is not implemented yet.  Currently, this command shows the reservation
status of the target, but not any online/network/booted status for the target board.

===== vars =====
Show information about variables and config files used by ttc

Usage: ttc [<target>] vars

===== version =====
Show version information and exit.

Usage: ttc version

===== wait_for =====
Wait for a condition to be true.

Usage: ttc [<target>] wait_for [-i <interval>] [-t <timeout>] <command>
The command is run periodically until it returns 0.  By default,
the interval between executing the command is 5 seconds.
Use -i to specify a different interval, and -t to specify a
maximum time to wait.  Both are expressed in seconds.

* Ex: ttc wait_for -i 2 -t 100 "test -f /target/ebony/tmp/outfile"

This will check every two seconds to see if /target/ebony/tmp/outfile exists,
waiting no longer than 100 seconds total. The exit code from
of 'ttc' is the exit code of the last invocation of the
command (0 on success).

Note that this command operates on the host.  The above example would
be most useful for an 'ebony' target with an NFS-mounted root filesystem
that had "/tmp" on the target mapped to "/target/ebony/tmp" on the host.
If you need to run a command on the target, you can use 'ttc run' for
that.  Some similar to the above, but running a command on the target
to check for the presence of a file would be:

* Ex: ttc wait_for -i 2 -t 100 "ttc run \"test -f /tmp/outfile\""

== Configuration files and environment variables ==
Configuring ttc consists of creating the definitions for ttc attributes and sub-commands for a target.
Note that more than one ttc entry can be created for a single physical board.  This is useful when 
you are working with different code-bases, different toolchains, or some other difference in configuration,
for a board.  For example, maybe you have a board which can run both Android and Angstrom.  You could have
two different ttc configurations for these different setups.

=== The global config file ===
The global config file for ttc is at /etc/ttc.conf.  If you do not have root access to your machine
(to put or edit stuff in /etc), then you should use a local config file instead.

=== Using a local config file ===
You can use a local ttc configuration file by creating the file, and specifying it's path in
the shell environment variable TTC_CONF. For example you could do the following to use a local
configuration file in your home directory:

* create ~/ttc.conf with your target definitions
* $ export TTC_CONF=~/ttc.conf
* $ ttc list

You can use a combination of both global and local configs, but in general it can get confusing
if you have the same targets in both config files.  Additionally, values are read from the
environment, and take precedence over any values set in the global and local config files.
For example, one variable set and used by ttc is ARCH.  If this is in your environment before
you run ttc, then the value from your environment is used instead of any values defined
from your ttc configuration.

The order of reading configuration values is:
# read the global config file (/etc/ttc.conf)
# read a local config file (if specified by TTC_CONF)
# read environment variables

== Automated use of 'ttc' ==
==== interactive vs. automated use ====
Some tricks for automated use:

Use the -o option with "ttc setenv" to output the environment variables to a file, then source that file in the current environment
This solves the problem of setting environment variables in the current shell, rather than in a sub-shell started via "ttc".
Here's a line which does this:

 ttc foo setenv -o >tmp ; source tmp ; rm tmp ; make $kimage

== Appendix A: Configuration file specification ==
The configuration file for <code>ttc</code> is named <code>"ttc.conf"</code>, and 
is located in the <code>/etc</code> directory.

This file contains a list of the targets attached to this host, and their
attributes.  An attribute can be a static data value, such as the name of the target,
its description, or its IP address. Or an attribute can be a list of one or more commands
that perform an operation related to the target. 

The file contains a list of name-value pairs.  It supports single-line and multi-line
values.  A single-line name-value pair has the syntax:
<pre>
name=value
</pre>

A multi-line name-value pair has the syntax:
<pre>
name="""first line
second line
etc."""
</pre>

In other words, three double-quotes are used to denote the start and end of
a multi-line value.

Lines starting with a '#' are comments. 

The file is divided into sections, one for each target described.  Each section
begins with a target declaration, of the form: "target=<name>". This
line specifies the end of the previous section (if any) and the start of a
new section.  The attributes that follow this line in the file are associated
with the indicated target, up to the next target declaration line.

Some values are sequences of shell script commands, which are used to 
implement a single <code>ttc</code> sub-command.
By convention, the names of an attribute which implement a command
ends with "_cmd".

If an attribute name is all upper-case, this denotes
a value that is placed in the environment.  (There are, however, some
environment variable values which are NOT denoted by an
upper-case attribute name).

Most attributes are put into the shell environment prior to execution of any '_cmd' scripts.
These attributes can be referenced by the scripts using shell variable syntax.  For example $KERNEL_SRC.
Attributes are also available internally for macro expansion using a python string interpolation
variable, like so: %(real_board)s.  The name of the attribute goes inside the parens, as in %(attr_name)s.
Make sure to include the trailing 's' in the reference, or python will throw an exception and things
will not work as you expect.  Note that string interpolation happens before a command is used
for external command execution.  (That is, before there is the shell substitutes environment variables.)

==== Configuration attributes summary ====

Supported attributes are:

{| border="1" cellpadding="5" cellspacing="0"
!style="background:#80cccc;"|'''Attribute Name'''
!style="background:#80cccc;"|'''Meaning of value'''
!style="background:#80cccc;"|'''Notes'''
|-
|target        ||Short (one-word) name of the target
|Names starting with '.' are hidden from 'ttc list'
|-
|real_board    ||"Real" name for the target board||This is used if the multiple target configurations are used with a single physical (real) target board.
|-
|inherit_from  ||Target to inherit attributes from.||Used to reference a common block of attributes.
|-
|description   ||A description of the target board.  Usually multi-line||This field is used for humans to let them know the attributes of the board.
|-
|TOOL_PATH     ||Path where toolchain tools are located.||This appended to the PATH env. variable.
|-
|ARCH          ||Architecture specifier for the kernel build (eg. arm, ppc, i386)||.
|-
|CROSS_COMPILE ||Toolchain prefix used with kernel builds (eg. arm-sony-linux- )||.
|-
|INSTALL_PATH  ||Place where kernel is installed||.
|-
|KERNEL_SRC    ||Default name to use for kernel source directory||.
|-
|KBUILD_OUTPUT ||Default directory for kernel build output||.
|-
|kimage        ||Name of the kernel image file (eg. bzImage, uImage)||.
|-
|kinstall_cmd  ||Command(s) to install the kernel image. ||Assumes that the current working dir is the top directory of the kernel source.
|-
|get_config_cmd||Command(s) to put a default kernel configuration file (.config) in $KBUILD_OUTPUT||.
|-
|get_kernel_cmd||Command(s) to put the kernel source code in $KERNEL_SRC||.
|-
|copy_to_cmd   ||Command(s) to copy files from host to target||Should reference $src and $dest
|-
|copy_from_cmd ||Command(s) to copy files from target to host||Should reference $src and $dest
|-
|rm_cmd        ||Command(s) to remove files from target||This command should reference $dest as the location on the target of the file(s) to be removed.
|-
|ipaddr        ||Target IP address||.
|-
|reboot_cmd    ||Command(s) to reboot the target, from the host
|This should power-cycle of the board, producing a cold boot of the hardware. 
|-
|reset_cmd     ||Command(s) to reset the target, from the host
|This is intended to be a soft reset of the hardware.
|-
|console_cmd   ||Command(s) to start an interactive console for the target.||This is usually something like minicom or screen.
|-
|login_cmd     ||Command(s) to start an interactive login session with the target||This is usually telnet, ssh or 'adb shell'.  Usually, multiple login commands can be started at one time to a single target.
|-
|target_bin    ||Directory on target where binary files are located||This can be used with 'ttc cp' to put executable files in a place on the target where they can be found using the target's PATH variable.
|-
|fsbuild_cmd   ||Command(s) to build a new filesystem image for the target||.
|-
|fsinstall_cmd ||Command(s) to install a new filesystem imgae for the target||.
|-
|run_cmd       ||Command to execute a command on the target||This command should reference $COMMAND as the string for the command to execute
|-
|reset_delay   ||Time in seconds to wait after reseting or rebooting the target||Only used if '-w' is used with 'ttc reboot' or 'ttc reset'
|}

==== Configuration attribute details ====
This section lists each configuration attribute, and what its value should be.

; target: Short (one-word) name of the target. If the target name starts with a '.', it is not displayed in the list from the command 'ttc list'.  This is similar to Linux directory listings, and is useful for having hidden targets, which other targets use as a base for inheritance.
; real_board: Name of the real board for a target.  This is a convention that allows multiple target configurations to be defined for a single board.  For example, you could have a real board "omap", and define different target configurations for working with the board using android, or directly with embedded linux (e.g. with target configurations for "omap-android" and "omap-linux".  The 'real_board' value is used for reserving the board and checking it's status.  It is often used in variable form in blocks that are inherited by other target configurations.
; inherit_from: Name of target configuration to inherit attributes from. Any attributes listed in the current target override attributes in the inherited-from target configuration.  A block that is inherited from may use %-style variable references to customize the commands in the block to the inheriting block.  For example, a inherited from block may specify kbuild_cmd as "kbuild_cmd=make %(kimage)s", and different inheriting targets could specify their own values for 'kimage' respectively.
; description: A description of the target board.  Usually this is a multi-line value, and is intended to provide information about the target in human-readable form.
; TOOL_PATH: Path where toolchain tools are located.  This appended to the PATH env. variable when a 'setenv' environment is constructed, and before any sub-commands are executed.
; ARCH: Architecture specifier for the kernel build (eg. arm, ppc, i386)
; CROSS_COMPILE: Toolchain prefix used with kernel builds (eg. arm-sony-linux- )
; INSTALL_PATH: Place where the kernel is installed
; KERNEL_SRC: Default name to use for kernel source directory
; KBUILD_OUTPUT: Default directory for kernel build output
; kimage: Name of the kernel image file (eg. bzImage, uImage)
; kinstall_cmd: Command(s) to install the kernel image.  (Assumes that the current working dir is $KERNEL_SRC)
; get_config_cmd: Command(s) to put a default kernel configuration file (.config) in $KBUILD_OUTPUT
; get_kernel_cmd: Command(s) to put the kernel source code in $KERNEL_SRC.
; copy_to_cmd: Command(s) to copy files from host to target.  This command should reference $src as the location of the file(s) on the host, and $dest as the location on the target for the copied file(s).
; copy_from_cmd: Command(s) to copy files from target to host. This command should reference $src as the location on the target to copy from, and $dest as the location on the host for the copied file(s).
; rm_cmd: Command(s) to remove files from target.  This command should reference $dest as the location on the target for the removed file(s).
; ipaddr: Target IP address
; reset_cmd: Command(s) to reset the target, from the host
; console_cmd: Command(s) to start an interactive console for the target (usually minicom)
; login_cmd: Command(s) to start an interactive login session with the target (usually telnet)
; target_bin: Directory on target where binary files are located
; fsbuild_cmd: Command(s) to build a root filesystem for the target
; fsinstall_cmd: Command(s) to install a root filesystem to the target
; reserve_cmd: Command(s) to reserve a board (like switching the root filesystem, in case of different users having different root filesystems)
; reboot_cmd: Command(s) to reboot the board.  This is intended to be a power-cycle of the board, producing a cold boot of the hardware.  Usually this is something like "powerswitch-cycle -n <board-name> -o 3 -d <some-delay>", but it depends on completely on how you have the board wired up for power and what the host needs to do to reboot it.  A helper command of powerswitch-cycle is provided for targets attached to web power switches from digital loggers. See http://www.digital-loggers.com/lpc.html.
; reset_cmd: Command(s) to reset the target, from the host. This is intended to be a soft reset of the hardware.  If you have automated control of a software reset pin or button on the board, then configure this command to activate it.  Otherwise, you could use something like: 'reset_cmd=ttc run reboot'
; run_cmd: Command to execute a command on the target.  This cmd should use $COMMAND as the string for the command to execute on target.  Some helper programs are provided to perform this execution using ssh or telnet (in case authentication or other handshaking is required to accomplish the execution.)  These are called ssh_exec and telnet_exec, respectively.

==== Configuration Example ====
Here is a sample:

<pre>
# Some notes on syntax and conventions
# Attributes that end in "_cmd" are assumed to be shell
# commands, which will be executed in shell context
# Each line of a multi-line _cmd will be executed
# in its own sub-shell.  (i.e. don't count on
# exports or cd's being persistent from one line to
# the next)
#
# The get_kernel_cmd should output the kernel source
# to the directory specified by $KERNEL_SRC
#======================================================
target=.telnet_defaults
description="""default commands and attributes for boards with telnet daemon,
root filesystem at /target/%(real_board)s (NFS-mounted),
and accessible via network at hostname %(real_board)s"""

login_cmd=telnet %(real_board)s
copy_to_cmd=cp $src /target/%(real_board)s/$dest
copy_from_cmd=cp /target/%(real_board)s/$src $dest
rm_cmd=rm /target/%(real_board)s/$dest
run_cmd=telnet_exec -t %(real_board)s -u root -c "$COMMAND"

#======================================================
target=innovator
real_board=inno-1
inherit_from=.telnet_defaults
description="""TI OMAP Innovator board, with:
OMAP1510 processor (ARM925T core and a C55x DSP)
The ARM core runs at 168 MHZ.
The board has 32 meg. of flash (in 2 16M banks) and
32 meg. of SDRAM."""

ipaddr=192.168.1.61
console_cm==minicom inno

TOOL_PATH=/usr/local/arm-sony-linux/devel/bin
ARCH=arm
CROSS_COMPILE=arm-sony-linux-
kimage=uImage
kinstall_cmd=cp -v arch/arm/boot/uImage /target/inno-1/boot
reset_cmd=omap-reset
get_kernel_cmd=export CVSRSH=/usr/bin/ssh ; cvs -d :ext:oak.sm.sony.co.jp:/var/cvsroot co -r branch_ALP_LINUX -d $KERNEL_SRC linux-2.6
get_config_cmd="""export CVSRSH=/usr/bin/ssh ; cvs -d :ext:oak.sm.sony.co.jp:/var/cvsroot co local-dev/team/configs
        cp local-dev/team/configs/config-innovator-baseline $KERNEL_SRC/.config"""

target_bin=/devel/usr/bin


#=================================================================================

target=osk
inherit_from=.telnet_defaults
real_board=osk2

description="""TI OMAP Starter Kit (OSK):
OMAP5912 processor (ARM926EJ-S core and a C55x DSP)
The ARM core runs at 192 MHZ.
The board has 32 meg. of flash and 32 meg. Mobile DDR SDRAM,
10 Mbit Ethernet interface, USB Host interface
and a AIC23 stereo codec."""

ipaddr=192.168.1.72
console_cmd=echo "console is on timdesk" ; false

TOOL_PATH=/usr/local/arm-sony-linux/devel/bin
ARCH=arm
CROSS_COMPILE=arm-sony-linux-
kimage=uImage
KERNEL_SRC==linux
TMPDIR=/tmp
KBUILD_OUTPUT=../build/osk
kinstall_cmd=cp -v $KBUILD_OUTPUT/arch/arm/boot/uImage /target/osk2/boot
reset_cmd=echo "remote reset not supported" ; false
get_kernel_cmd=tla get -A alp@oak--trial-5 alp-linux--dev $KERNEL_SRC
get_config_cmd="""export CVSRSH==/usr/bin/ssh ; cd $TMPDIR ; cvs -d :ext:oak.sm.sony.co.jp:/var/cvsroot co local-dev/team/configs/config-osk-baseline ; cd -
        cp $TMPDIR/local-dev/team/configs/config-osk-baseline $KBUILD_OUTPUT/.config"""

target_bin=/devel/usr/bin

#==================================================================================================
target=nut
inherit_from=.telnet_defaults
real_board=nut
description=="""Nut is an x86-based desktop computer, with:
Intel Celeron processor, running at 2 GHz.
The machine has 128 meg. of RAM and a 40G IDE hard drive."""

reset_cmd=nut-reset
console_cmd=minicom nut

ipaddr=192.168.1.14

TOOL_PATH=
ARCH=
CROSS_COMPILE=
INSTALL_PATH=/target/nut/boot
KERNEL_SRC=linux
KBUILD_OUTPUT=../build/nut

kimage=bzImage
kinstall_cmd=cp -v $KBUILD_OUTPUT/arch/i386/boot/bzImage /target/nut/boot/vmlinuz
get_kernel_cmd="""tar -xjf /home/rbatest/base/linux-2.6.10.tar.bz2
                mv linux-2.6.10 $KERNEL_SRC"""
get_config_cmd=cp /home/rbatest/base/config-nut-works-2.6.11-rc4 $KBUILD_OUTPUT/.config
</pre>

== Appendix B: Configuration tips and tricks ==
Should document the following here:
=== Helper Programs included with ttc ===
* use of helper programs:
** telnet_exec, ssh_exec - used to execute commands on the target, communicating either with a telnet daemon or ssh daemon (and handling things like specifying the user and password).
** powerswitch-cycle - used to reboot boards attached to a Digital Loggers web power switch
** switch-target-fs - used to switch between root filesystems when 'ttc reserve' is used
=== Using inheritance ===
* inheritance and multiple target configurations for a single board
=== Tips for setting up a board reservation system ===
* reserving boards
=== Using an all-networked deployment system ===
* using tftp for kernel and NFS rootfs for filesystem

=== Using ttc with SDcard-based systems ===
* how to use a baseline (known working) kernel & rootfs with sdcard-based systems
** configure SDcard with multiple partitions
** configure uboot with timed delay
** interrupt uboot from host by writing to serial console
** select either known-working kernel or kernel-under-test to boot
** for kinstall_cmd reboot to known-working kernel and use that kernel to write system under test to other partitions on SDCARD
** for reboot_cmd, reboot to test kernel.

=== Using ttc with Android systems ===
* how to wrap adb for android systems
** Can use setenv_cmd to check for correct Android configuration

Here is a snippet from a target configuration for an android-based device:
<pre>
setenv_cmd="""if [ -z "$ANDROID_BUILD_TOP" ] ; then \
        echo "ANDROID_BUILD_TOP is not set - please source build/envsetup.sh" ;  \
        exit 1 ; \
fi
"""

TOOL_PATH=$ANDROID_BUILD_TOP/prebuilts/gcc/linux-x86/arm/arm-eabi-4.6/bin
CROSS_COMPILE=ccache arm-eabi-
ARCH=arm
kimage=zImage
KBUILD_OUTPUT=../out/kbuild/%(target)s
INSTALL_MOD_PATH=../modules/%(target)s
KERNEL_SRC=kernel
TMPDIR=/tmp

kbuild_cmd=time make -j8 %(kimage)s
login_cmd=adb shell
copy_to_cmd=adb push $src $dest
copy_from_cmd=adb pull $src $dest
rm_cmd=adb shell rm $dest
run_cmd=adb shell "$COMMAND"

</pre>

** specify prebuilt toolchains relative to $ANDROID_BUILD_TOP
** use 'adb push' for copy_to_cmd, and 'adb pull' for copy_from_cmd.
** use 'adb shell' for run_cmd

=== Using ttc with a distribution produced with the Yocto Project ===
* integration with Yocto Project

