# (C) 2012, Michael DeHaan, <michael.dehaan@gmail.com>

# This file is part of Ansible
#
# Ansible is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Ansible is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Ansible.  If not, see <http://www.gnu.org/licenses/>.

# Make coding more python3-ish
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

from ansible.plugins.callback import CallbackBase
import zmq
import random
import sys
import time
import json
import uuid
import os

class UUIDSafeEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, uuid.UUID):
            return str(obj)
            # Let the base class default method raise the TypeError
        return json.JSONEncoder.default(self, obj)


class CallbackModule(CallbackBase):
    """
    This is a very trivial example of how any callback function can get at play and task objects.
    play will be 'None' for runner invocations, and task will be None for 'setup' invocations.
    """
    CALLBACK_VERSION = 2.0
#    CALLBACK_TYPE = 'aggregate'
#    CALLBACK_NAME = 'context_demo'
#    CALLBACK_NEEDS_WHITELIST = True

    def __init__(self, *args, **kwargs):
        self.task = None
        self.play = None

        self.context = zmq.Context()
        self.socket = self.context.socket(zmq.PUB)

        try:
            self.socket.bind(os.environ['DAUBER_SOCKET_URI'])
        except KeyError:
            pass

    def v2_runner_on_failed(self, result, ignore_errors):
        pass

    def v2_runner_on_ok(self, result):
        pass

    def v2_runner_on_skipped(self, result):
        pass

    def v2_runner_on_unreachable(self, result):
        pass

    def v2_playbook_on_no_hosts_matched(self):
        pass

    def v2_playbook_on_no_hosts_remaining(self):
        pass

    def v2_playbook_on_task_start(self, task, is_conditional):
        self.task = task
        msg = "%s %s" % ('on_task_start', json.dumps(self.task.serialize(), cls=UUIDSafeEncoder))
        self.socket.send(msg)

    def v2_playbook_on_cleanup_task_start(self, task):
        pass

    def v2_playbook_on_handler_task_start(self, task):
        pass

    def v2_playbook_on_play_start(self, play):
        pass

    def v2_on_any(self, *args, **kwargs):
        pass

    def v2_on_file_diff(self, result):
        pass

    def v2_runner_item_on_ok(self, result):
        pass

    def v2_runner_item_on_failed(self, result):
        pass

    def v2_runner_item_on_skipped(self, result):
        pass

    def v2_playbook_on_include(self, included_file):
        pass

    def v2_playbook_on_stats(self, stats):
        pass

    def v2_playbook_on_start(self, playbook):
        pass

    def v2_runner_retry(self, result):
        pass
