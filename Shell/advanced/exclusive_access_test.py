#!/usr/bin/python
#
# Exclusive access test for the shell.
# 
# This file is based on the /basic/ test cases provided to us: 
# 		bg_test, ctrl-c_test, ctrl-z_test, fg_test, jobs_test, kill_test, and stop_test
#
#	In particular, this test is HEAVILY based on the CTRL-Z and STOP tests given to us.
#
import sys, imp, atexit
sys.path.append("/home/courses/cs3214/software/pexpect-dpty/");
import pexpect, shellio, signal, time, os, re, proc_check

# Ensure the shell process is terminated
def force_shell_termination(shell_process):
	c.close(force=True)

# pulling in the regular expression and other definitions
definitions_scriptname = sys.argv[1]
def_module = imp.load_source('', definitions_scriptname)
logfile = None
if hasattr(def_module, 'logfile'):
    logfile = def_module.logfile

# spawn an instance of the shell
c = pexpect.spawn(def_module.shell, drainpty=True, logfile=logfile)
atexit.register(force_shell_termination, shell_process=c)

# set default timeout to 2 seconds 
c.timeout = 2

# ensure that shell prints expected prompt
assert c.expect(def_module.prompt) == 0, "Shell did not print expected prompt"

# run a command
c.sendline("vim exclusive_fruit_access")

# The following call is necessary to ensure that the SIGTSTP
# we are sending below via 'sendcontrol' reaches the 'sleep' child.
proc_check.wait_until_child_is_in_foreground(c)

# checks the number of active child processes
# using a timeout based process count
proc_check.count_children_timeout(c, 1, 1)

# checks the number of active child processes
# at this moment in time
proc_check.count_active_children(c, 1)

# send SIGTSTP to 'sleep'
c.sendcontrol('z')

# shell should pick up that 'sleep' was stopped and respond with job status
# it should output a line such as [6]+  Stopped                 (sleep 60)
# (note that the provided regexp assumes the job name appears in parentheses,
# adjust your eshoutput.py if needed)
(jobid, statusmsg, cmdline) = \
        shellio.parse_regular_expression(c, def_module.job_status_regex)

assert statusmsg == def_module.jobs_status_msg['stopped'], "Shell did not report stopped job"

# move job into foreground
c.sendline(def_module.builtin_commands['fg'] % jobid)

# exit
c.sendline(":q!")

# when moving a job in the foreground, bash outputs its command line
assert c.expect_exact(cmdline) == 0, "Shell did not report the job moved into the foreground"

# send nano into the background
c.sendline("nano &")

# print out a list of the jobs
c.sendline(def_module.builtin_commands['jobs'])

(jobid, statusmsg, cmdline) = \
        shellio.parse_regular_expression(c, def_module.job_status_regex)

assert statusmsg == def_module.jobs_status_msg['stopped'], "Shell did not report stopped job (nano)"

# exit
c.sendline("exit")
assert c.expect_exact("exit\r\n") == 0, "Shell output extraneous characters"

shellio.success()
