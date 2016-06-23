from __future__ import print_function
from playbook import Playbook
import zmq
import json
from pprint import pprint
import os
import subprocess
import logging
import tempfile
import shutil
import pkg_resources as pr
import sys

class ZMQPlaybook(Playbook):

    def __init__(self, *args, **kwargs):
        super(ZMQPlaybook, self).__init__(*args, **kwargs)
        self._sockets = []
        self._hooks = {}

        self.context = kwargs.get("context", zmq.Context.instance())
        self.socket = self.context.socket(zmq.SUB)
        self.socket.setsockopt(zmq.SUBSCRIBE, 'v2_playbook_on_task_start')

        self.socket_dir = tempfile.mkdtemp()
        self._env['DAUBER_SOCKET_URI'] = "ipc://{}/dauber.socket".format(self.socket_dir)
        self.socket.connect(self._env['DAUBER_SOCKET_URI'])

        self.poller = zmq.Poller()
        self._register_socket(self.socket, self.__class__._zmq_socket_handler)

        self.add_callback_plugin_dir(
            pr.resource_filename(__name__, 'ansible/callback_plugins'))

        self.logger.setLevel(logging.DEBUG)
        self.verbosity = 3

    def _register_socket(self, socket, callback, opt=zmq.POLLIN):
        self.poller.register(socket, opt)
        self._sockets.append((socket, callback, opt))

    def _zmq_socket_handler(self, socket):
        string = socket.recv()
        json0 = string.find('{')
        topic, msg = string[0:json0].strip(), json.loads(string[json0:])
        pprint(msg)


    def _ansible_stdout_handler(self, stdout):
        self.logger.debug(stdout.readline().strip())

    def _ansible_stderr_handler(self, stderr):
        self.logger.debug(stderr.readline().strip())


    def _run(self):
        self.logger.debug(self.cmd)
        p = subprocess.Popen(self.cmd, env=self._env, stdout=subprocess.PIPE,
                             stderr=subprocess.PIPE)
        self._register_socket(p.stdout, self.__class__._ansible_stdout_handler)
        self._register_socket(p.stderr, self.__class__._ansible_stderr_handler)

        while True:
            ready = dict(self.poller.poll())
            for socket, callback, opt in self._sockets:
                try:
                    if socket.fileno() in ready and ready[socket.fileno()] == zmq.POLLIN:
                        callback(self, socket)
                except AttributeError:
                    if socket in ready and ready[socket] == zmq.POLLIN:
                        callback(self, socket)

            if p.poll() is not None:
                break

        return p.wait()

    def cleanup(self):
        super(ZMQPlaybook, self).cleanup()
        try:
            shutil.rmtree(self.socket_dir)
        except OSError:
            pass


# context = zmq.Context()
# socket = context.socket(zmq.SUB)
# socket.setsockopt(zmq.SUBSCRIBE, 'on_task_start')
# socket.connect ("tcp://localhost:5556")
#
# while True:
#     string = socket.recv()
#     json0 = string.find('{')
#     topic = string[0:json0].strip()
#     msg = json.loads(string[json0:])
#
#     print(topic)
#     pprint(msg)
