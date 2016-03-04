# ttc
Tim's Target Control program

## Introduction
This is the README for the 'ttc' program. This program was originally written
for use with the CE Linux Forum Open Test Lab.  This program has been used
internally at Sony by its Linux kernel and distribution teams for many years.

## Installation
To install, copy 'ttc' to /usr/local/bin.  Create your own /etc/ttc.conf
file to reflect the setup of your host/target combination.  (See the
ttc.conf.sample file provided).  Also, put any required helper scripts
in your PATH.

Some helper scripts are provided:
 * telnet_exec is for running a command on another machine via telnet.
     It is used in the sample ttc.conf.
 * ssh_exec is for running a command on another machine via ssh.
     It is used in the sample ttc.conf.
 * preset-test.py is a sample test program which shows how to use
     ttc to run a series of tests on a target machine.
 * config-sizes-test.py is a sample test program which shows how to use
     ttc to run a series of tests on a target machine.

== Resources
Online documentation is available at:
http://elinux.org/Ttc_Program_Usage_Guide

== Authorship
Author: 'ttc' was written by Tim Bird, <tim.bird (at) sonymobile.com>
Copyright: (c) 2005-2016 Sony Corporation
