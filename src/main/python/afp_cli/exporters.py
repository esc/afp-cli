#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import print_function, absolute_import, division

import os
import subprocess
import sys
import tempfile

RC_SCRIPT_TEMPLATE = """
# Pretend to be an interactive, non-login shell
for file in /etc/bash.bashrc ~/.bashrc; do
    [ -f "$file" ] && . "$file"
done

function afp_minutes_left {{
    if ((SECONDS >= {valid_seconds})) ; then
        echo EXPIRED
    else
        echo $((({valid_seconds}-SECONDS)/60)) Min
    fi
}}

PS1="(AWS {account}/{role} \\$(afp_minutes_left)) $PS1"
"""

BATCH_FILE_TEMPLATE = """
@echo off
set PROMPT=$C AWS {account}/{role} $F
"""


def format_aws_credentials(credentials, prefix=''):
    """Format aws credentials with optional prefix"""
    return os.linesep.join(["{0}{1}='{2}'".format(prefix, key, value)
                            for (key, value) in sorted(credentials.items())])


def format_account_and_role_list(account_and_role_list):
    return os.linesep.join(["{0:<20} {1}".format(account, ",".join(sorted(roles)))
                            for account, roles in sorted(account_and_role_list.items())])


def start_subshell(aws_credentials, role, account):
    print("Press CTRL+D to exit.")
    rc_script = tempfile.NamedTemporaryFile(mode='w')
    rc_script.write(RC_SCRIPT_TEMPLATE.format(role=role, account=account,
                                              valid_seconds=aws_credentials['AWS_VALID_SECONDS']))
    rc_script.write(format_aws_credentials(aws_credentials, prefix='export '))
    rc_script.flush()
    subprocess.call(
        ["bash", "--rcfile", rc_script.name],
        stdout=sys.stdout, stderr=sys.stderr, stdin=sys.stdin)
    print("Left AFP subshell.")


def start_subcmd(aws_credentials, role, account):
    batch_file = tempfile.NamedTemporaryFile(suffix=".bat", delete=False)
    batch_file.write(BATCH_FILE_TEMPLATE.format(role=role, account=account))
    batch_file.write(format_aws_credentials(aws_credentials, prefix='set '))
    batch_file.flush()
    batch_file.close()
    subprocess.call(
        ["cmd", "/K", batch_file.name])
    print("Left AFP subcmd.")
    os.unlink(batch_file.name)
