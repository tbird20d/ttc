#!/usr/bin/python3
# uboot-env-dump.py - dump the value
# created by Grok on 2025-05-07 with the prompt:
# what is the binary format of uboot.env files?
#
# Modifications and enhancements by Tim Bird
# Copyright 2025 Sony Group Corporation
#

import binascii
import struct
import os
import sys

debug = False

def error_out(msg):
    print("Error: " + msg)
    exit(1)

def usage(rcode):
    print("""Usage uboot-env-edit.py [-f <filename>] [<expression>]

Show or edit the contents of specified uboot.env file.
If no filename provided, use the filename  'uboot.env'

With no options, will show the value of all variables in the file.

Options:
 -f <filename>    Specify input file.  Defaults to 'uboot.env'
 -o <filename>    Specify output file.
 -q               Quiet mode. Don't print the CRC status, or extraneous
                  information.

Allowed expressions:
 <var>            Show value of variable <var>
 <var>=<value>    Set variable <var> value to <value>
 <var>=           Remove variable <var>
 <var>+=<value>   Append <value> to variable <var>
 <var>-=<value>   Remove <value> from variable <var>
""")
    sys.exit(rcode)

def get_opt_with_arg(arg):
    try:
        arg_pos = sys.argv.index(arg)
        var = sys.argv[arg_pos + 1]
        del sys.argv[arg_pos + 1]
        del sys.argv[arg_pos]
    except IndexError:
        error_out("Missing argument to '%s'. Use -h for help" % arg)

    return var

def get_value_or_error_out(env_vars, name):
    try:
        value = env_vars[name]
    except:
        error_out("Variable '%s' not found in environment" % name)
    return value

def main():
    filename = "uboot.env"
    out_file = ""
    verbose = True

    # parse arguments
    if "-h" in sys.argv:
        usage(0)

    if "-f" in sys.argv:
        filename = get_opt_with_arg("-f")

    if "-o" in sys.argv:
        out_file = get_opt_with_arg("-o")

    if "-q" in sys.argv:
        sys.argv.remove("-q")
        verbose = False

    expr = ""
    try:
        expr = " ".join(sys.argv[1:])
    except:
        pass

    if not os.path.isfile(filename):
        error_out("File not found: '%s'" % filename)

    try:
        with open(filename, "rb") as f:
           data = f.read()
    except:
        error_out("Cannot read file: '%s'" % filename)
        sys.exit(1)

    orig_size = len(data)
    orig_pad_byte = data[-1]

    crc_stored = struct.unpack("<I", data[0:4])[0]
    env_data = data[4:]

    if debug:
        print("orig_size=%d" % orig_size)
        print("len(data)=%d" % len(data))
        print("(index) orig_pad_byte s=%s" % orig_pad_byte)
        print("oriiginal len(env_data)=%d" % len(env_data))

    crc_calc = binascii.crc32(env_data) & 0xFFFFFFFF
    if verbose:
        if crc_stored == crc_calc:
            print("CRC is OK")
        else:
            print("CRC mismatch!!")

    # Parse variables
    env_vars={}
    env_list=[]
    shown = False
    for s in env_data.split(b'\0'):
        if not s:
            break
        key, value = s.split(b'=', 1)
        key = key.decode()
        value = value.decode()
        env_vars[key] = value
        env_list.append(key)
        if not expr or expr == key :
            print("%s=%s" % (key, value))
            shown = True

    if shown:
        #we're done
        sys.exit(0)

    ##########################
    # handle modifications

    # parse expr
    if "=" in expr:
        if "+=" in expr:
            # append to value
            name, value = expr.split("+=",1)
            old_value = get_value_or_error_out(env_vars, name)
            env_vars[name] = old_value + " " + value
            if verbose:
                print("'%s' appended to value:" % value)
        elif "-=" in expr:
            # remove from value
            name, value = expr.split("-=",1)
            old_value = get_value_or_error_out(env_vars, name)
            if not value in old_value:
                error_out("Value '%s' not found in '%s=%s'" % (value, name, old_value))
            if verbose:
                print("Removing '%s' from value:" % value)
        else:
            # set or remove variable
            name, value = expr.split("=",1)
            if not value:
                # this is a variable remove
                junk = get_value_or_error_out(env_vars, name)
                env_list.remove(name)
                del env_vars[name]
                if verbose:
                    print("Variable '%s' removed:" % name)
            else:
                if name not in env_vars:
                    # this is a new variable addition, add to list
                    env_list.append(name)

                # this is a varible update
                env_vars[name] = value
                if verbose:
                    print("Value set:")

        if value:
            print("%s=%s" % (name, env_vars[name]))

    if not out_file:
        error_out("No output file specified")

    # write out new stuff
    # keep order the same
    new_env_data = b""
    for var in env_list:
        new_var_def = ("%s=%s" % (var, env_vars[var]))
        new_env_data += (new_var_def.encode() + b'\0')

    new_env_data += b'\0'

    # Pad with pad_byte to exact size
    pad_byte = orig_pad_byte
    # 4 = CRC size
    pad_len = orig_size - 4 - len(new_env_data)
    padding = bytes([pad_byte] * pad_len)

    new_data = new_env_data + padding
    new_crc_calc = binascii.crc32(new_data) & 0xFFFFFFFF
    new_crc = struct.pack("<I", new_crc_calc)

    if debug:
        print("len(padding) (as bytes([pad_byte] * pad_len) =%d" % len(padding))
        chunk = padding[0:15]
        hex_str = " ".join([f'{b:02x}' for b in chunk])
        print("first part of padding=%s" % hex_str)

        print("orig_size=%d" % orig_size)
        print("len(new_crc)=%d" % len(new_crc))
        print("len(new_env_data)=%d" % len(new_env_data))
        print("len(padding)=%d" % len(padding))
        full_size = len(new_crc) + len(new_env_data) + len(padding)
        print("full_size=%d" % full_size)

    with open(out_file, "wb") as fd:
        fd.write(new_crc)
        fd.write(new_data)

    if verbose:
        print("File '%s' written with new data." % out_file)

if __name__ == "__main__":
    main()

