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
import time

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
#    'v2_playbook_on_start', # See note on function
    'v2_runner_retry',
]

def pluck(fields):
    def _serialize(obj):
        return {k: getattr(obj, k) for k in fields if hasattr(obj, k)}

    return _serialize


class CustomEncoder(json.JSONEncoder):
    class_map = {
        uuid.UUID: str,
        Playbook: pluck(['_file_name', '_basedir', '_entries']),
        Task: Task.serialize,
        Play: Play.serialize,
        Block: Block.serialize,
        TaskResult: pluck(['_result', '_task']),
        AggregateStats: pluck(['ok', 'changed', 'failures', 'skipped', 'processed'])
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

#    def v2_playbook_on_include(self, included_file):
#         from pudb.remote import set_trace; set_trace(term_size=(319, 89))
#         self.publish('v2_playbook_on_include', included_file)

    # This has to be defined outside of the automatic hook generation because
    # of the ansible magic here:
    # https://github.com/ansible/ansible/blob/devel/lib/ansible/executor/task_queue_manager.py#L340-L352
    def v2_playbook_on_start(self, playbook):
        self.publish('v2_playbook_on_start', playbook)


    # See: http://zguide.zeromq.org/page:all#toc47
    def _wait_for_goahead(self):
        control_socket = self.context.socket(zmq.REP)
        control_socket.bind(os.environ['DAUBER_CONTROL_SOCKET_URI'])

        poller = zmq.Poller()
        poller.register(control_socket)

        timeout = 500
        t_last = time.time()
        while (time.time() - t_last) < timeout:
            ready = dict(poller.poll(10))
            if ready.get(control_socket):
                control_socket.recv()

                control_socket.send(b'')

                break

            self.socket.send_multipart(['hello', b''])
            t_last = time.time()

        assert (time.time() - t_last) < timeout, \
            "Timed out before recieving a signal to continue"

        del control_socket


    def __init__(self, *args, **kwargs):
        self.context = zmq.Context()
        self.socket = self.context.socket(zmq.PUB)
        try:
            self.socket.bind(os.environ['DAUBER_SOCKET_URI'])

            # Slow joiner problem
            # time.sleep(0.2)
        except KeyError:
            # What do now?
            pass

        # Make sure we've got the go-ahead from the subscriber before
        # we start publishing data (solves late joiner problem more
        # robustly than by just 'sleeping'
        self._wait_for_goahead()

    def publish(self, topic, *args, **kwargs):
        self.socket.send_multipart(
            [topic, json.dumps(args, cls=CustomEncoder),
             json.dumps(kwargs, cls=CustomEncoder)])


# Proxy through all hooks to publish
def add_hook(hook):
    def _hook(self, *args, **kwargs):
        self.publish(hook, *args, **kwargs)
    return _hook

for hook in HOOK_NAMES:
    setattr(CallbackModule, hook, add_hook(hook))
