from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import ansible
from ansible.executor.task_result import TaskResult
from ansible.executor.stats import AggregateStats
from ansible.playbook import Playbook, Play
from ansible.playbook.task import Task
from ansible.playbook.block import Block

import zmq
import random
import sys
import time
import json
import uuid
import os


HOOK_NAMES = [
    'v2_runner_on_failed',
    'v2_runner_on_ok',
    'v2_runner_on_skipped',
    'v2_runner_on_unreachable',
    'v2_playbook_on_no_hosts_matched',
    'v2_playbook_on_no_hosts_remaining',
    'v2_playbook_on_task_start',
    'v2_playbook_on_cleanup_task_start',
    'v2_playbook_on_handler_task_start',
    'v2_playbook_on_play_start',
    'v2_on_any',
    'v2_on_file_diff',
    'v2_runner_item_on_ok',
    'v2_runner_item_on_failed',
    'v2_runner_item_on_skipped',
    'v2_playbook_on_include',
    'v2_playbook_on_stats',
    'v2_playbook_on_start',
    'v2_runner_retry'
]

def pluck(fields):
    def _serialize(self, obj):
        return {k: getattr(k, obj) for k in fields if hasattr(k, obj)}

    return _serialize



class CustomEncoder(json.JSONEncoder):
    class_map = {
        uuid.UUID: str,
        Playbook: pluck(['_file_name', '_basedir', '_entries']),
        Task: Task.serialize,
        Play: Play.serialize,
        Block: Block.serialize,
        TaskResult: lambda tr: tr._result,
        AggregateStats: AggregateStats.__repr__
    }

    def default(self, obj):
        for cls, func in self.class_map.items():
            if isinstance(obj, cls):
                return func(obj)

        return json.JSONEncoder.default(self, obj)


class CallbackModule(ansible.plugins.callback.CallbackBase):
    """
    This is a callback designed to create a local IPC based zmq socket
    for publishing ansible events and data to be consumed by other objects
    such as dauber's ZMQPlaybook object.
    """
    CALLBACK_VERSION = 2.0
    CALLBACK_TYPE = 'notification'
    CALLBACK_NAME = 'zmq'


    def __init__(self, *args, **kwargs):

        self.context = zmq.Context()
        self.socket = self.context.socket(zmq.PUB)

        try:
            self.socket.bind(os.environ['DAUBER_SOCKET_URI'])
        except KeyError:
            # What do now?
            pass

    def publish(self, topic, obj):
        msg = "%s %s" % (topic, json.dumps(obj, cls=CustomEncoder))
        self.socket.send(msg)

# Proxy through all hooks to publish
def add_hook(hook):
    def _hook(self, *args, **kwargs):
        self.publish(hook, {'args': args, 'kwargs': kwargs})
    return _hook

for hook in HOOK_NAMES:
    setattr(CallbackModule, hook, add_hook(hook))


#     def v2_runner_on_failed(self, result, ignore_errors):
#         pass
#
#     def v2_runner_on_ok(self, result):
#         pass
#
#     def v2_runner_on_skipped(self, result):
#         pass
#
#     def v2_runner_on_unreachable(self, result):
#         pass
#
#     def v2_playbook_on_no_hosts_matched(self):
#         pass
#
#     def v2_playbook_on_no_hosts_remaining(self):
#         pass
#
#     def v2_playbook_on_task_start(self, task, is_conditional):
#         pass
#
#     def v2_playbook_on_cleanup_task_start(self, task):
#         pass
#
#     def v2_playbook_on_handler_task_start(self, task):
#         pass
#
#     def v2_playbook_on_play_start(self, play):
#         pass
#
#     def v2_on_any(self, *args, **kwargs):
#         pass
#
#     def v2_on_file_diff(self, result):
#         pass
#
#     def v2_runner_item_on_ok(self, result):
#         pass
#
#     def v2_runner_item_on_failed(self, result):
#         pass
#
#     def v2_runner_item_on_skipped(self, result):
#         pass
#
#     def v2_playbook_on_include(self, included_file):
#         pass
#
#     def v2_playbook_on_stats(self, stats):
#         pass
#
#     def v2_playbook_on_start(self, playbook):
#         pass
#
#     def v2_runner_retry(self, result):
#         pass
