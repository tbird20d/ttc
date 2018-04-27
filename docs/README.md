# ttc
Tim's Target Control program

## Introduction
This is the README for the 'ttc' program. This program was originally written
for use with the CE Linux Forum Open Test Lab.  This program has been used
internally at Sony by its Linux kernel and distribution teams for many years.

## Installation
Try 'sudo ./install.sh /usr/local/bin'

To install, copy 'ttc' and the helper scripts to somewhere on your PATH.
Then create your own /etc/ttc.conf file to reflect the setup of your
host/target combination.  (See the ttc.conf.sample file provided).

Some helper scripts are provided:
 * telnet_exec is for running a command on another machine via telnet.
     It is used in the sample ttc.conf.
 * ssh_exec is for running a command on another machine via ssh.
     It is used in the sample ttc.conf.
 * target-test.py tests different features of ttc to see if a particular
     target supports those features
 * preset-test.py is a sample test program which shows how to use
     ttc to run a series of tests on a target machine.
 * config-sizes-test.py is a sample test program which shows how to use
     ttc to run a series of tests on a target machine.

## Resources
Online documentation is available at:
http://elinux.org/Ttc_Program_Usage_Guide

## Authorship
Author: 'ttc' was written by Tim Bird, <tim.bird (at) sonymobile.com>
Copyright: (c) 2005-2016 Sony Corporation
