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

        self.context = kwargs.get("context", zmq.Context.instance())
        self.socket = self.context.socket(zmq.SUB)
        self.socket.setsockopt(zmq.SUBSCRIBE, 'on_task_start')

        self.socket_dir = tempfile.mkdtemp()
        self._env['DAUBER_SOCKET_URI'] = "ipc://{}/dauber.socket".format(self.socket_dir)
        self.socket.connect(self._env['DAUBER_SOCKET_URI'])

        self.poller = zmq.Poller()
        self.poller.register(self.socket, zmq.POLLIN)

        self.add_callback_plugin_dir(
            pr.resource_filename(__name__, 'ansible/callback_plugins'))

        self.logger.setLevel(logging.INFO)
        self.verbosity = 3

    def _run(self):
        self.logger.debug(self.cmd)


        p = subprocess.Popen(self.cmd, env=self._env, stdout=subprocess.PIPE,
                             stderr=subprocess.PIPE)

        self.poller.register(p.stdout, zmq.POLLIN)
        self.poller.register(p.stderr, zmq.POLLIN)

        should_continue = True
        while should_continue:

            socks = dict(self.poller.poll())

            if self.socket in socks and socks[self.socket] == zmq.POLLIN:
                string = self.socket.recv()
                json0 = string.find('{')
                topic = string[0:json0].strip()
                msg = json.loads(string[json0:])
                print(topic)
                pprint(msg)


            if p.poll() is not None:
                should_continue = False

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
