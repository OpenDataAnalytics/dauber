from __future__ import print_function
from playbook import Playbook
import zmq
import json
import subprocess
import logging
import tempfile
import shutil
import pkg_resources as pr
import time

ANSIBLE_HOOK_TOPICS = [
    'v2_runner_on_failed',                # def v2_runner_on_failed(result, ignore_errors):
    'v2_runner_on_ok',                    # def v2_runner_on_ok(result):
    'v2_runner_on_skipped',               # def v2_runner_on_skipped(result):
    'v2_runner_on_unreachable',           # def v2_runner_on_unreachable(result):
    'v2_playbook_on_no_hosts_matched',    # def v2_playbook_on_no_hosts_matched():
    'v2_playbook_on_no_hosts_remaining',  # def v2_playbook_on_no_hosts_remaining():
    'v2_playbook_on_task_start',          # def v2_playbook_on_task_start(task, is_conditional):
    'v2_playbook_on_cleanup_task_start',  # def v2_playbook_on_cleanup_task_start(task):
    'v2_playbook_on_handler_task_start',  # def v2_playbook_on_handler_task_start(task):
    'v2_playbook_on_play_start',          # def v2_playbook_on_play_start(play):
    'v2_on_any',                          # def v2_on_any(*args, **kwargs):
    'v2_on_file_diff',                    # def v2_on_file_diff(result):
    'v2_runner_item_on_ok',               # def v2_runner_item_on_ok(result):
    'v2_runner_item_on_failed',           # def v2_runner_item_on_failed(result):
    'v2_runner_item_on_skipped',          # def v2_runner_item_on_skipped(result):
    'v2_playbook_on_include',             # def v2_playbook_on_include(included_file):
    'v2_playbook_on_stats',               # def v2_playbook_on_stats(stats):
    'v2_playbook_on_start',               # def v2_playbook_on_start(playbook):
    'v2_runner_retry'                     # def v2_runner_retry(result):
]

class ZMQPlaybook(Playbook):

    def __init__(self, *args, **kwargs):
        super(ZMQPlaybook, self).__init__(*args, **kwargs)
        self._sockets = []
        self._hooks = {}

        self.context = kwargs.get("context", zmq.Context.instance())
        self.socket = self.context.socket(zmq.SUB)

        self.socket_dir = tempfile.mkdtemp()
        self._env['DAUBER_SOCKET_URI'] = "ipc://{}/dauber.socket".format(self.socket_dir)
        self.socket.connect(self._env['DAUBER_SOCKET_URI'])

        self._env['DAUBER_CONTROL_SOCKET_URI'] = "ipc://{}/control.socket".format(self.socket_dir)

        self.poller = zmq.Poller()
        self._register_socket(self.socket, self.__class__._zmq_socket_handler)

        self.add_callback_plugin_dir(
            pr.resource_filename(__name__, 'ansible/callback_plugins'))

        self.logger.setLevel(logging.WARNING)

        self.verbosity = 4

    def add_hook(self, hook, callback):
        assert hook in ANSIBLE_HOOK_TOPICS, \
            "%s is not defined in ANSIBLE_HOOK_TOPICS" % hook
        if hook not in self._hooks:
            self._hooks[hook] = []

        self.socket.setsockopt(zmq.SUBSCRIBE, hook)

        self._hooks[hook].append(callback)

    # This is a "private" API for registering sockets on the the polling loop
    def _register_socket(self, socket, callback, opt=zmq.POLLIN):
        self.poller.register(socket, opt)
        self._sockets.append((socket, callback, opt))

    def _zmq_socket_handler(self, socket):
        topic, args, kwargs = socket.recv_multipart()

        self.logger.debug("Recieved notification on topic: {}".format(topic))
        args = json.loads(args)
        kwargs = json.loads(kwargs)

        if topic not in self._hooks or not self._hooks[topic]:
            self.logger.warn("Listening on {}, but no topic hook is defined. "
                             "Doing nothing.".format(topic))
        else:
            for callback in self._hooks[topic]:
                callback(*args, **kwargs)


    def _ansible_stdout_handler(self, stdout):
        #        self.logger.info(stdout.readline().strip())
        pass

    def _ansible_stderr_handler(self, stderr):
        self.logger.error(stderr.readline().strip())

    # see: http://zguide.zeromq.org/page:all#toc47
    def _connect(self):
        # Subscribe to the hello topic - once we recieve a hello we'll send a request
        # for real data.  The callback plugin will effectively block execution until we
        # Send this request
        self.socket.setsockopt(zmq.SUBSCRIBE, 'hello')

        # Define the control socket for responding to the 'hello' topic
        control_socket = self.context.socket(zmq.REQ)
        control_socket.connect(self._env['DAUBER_CONTROL_SOCKET_URI'])
        timeout = 500
        t_last = time.time()
        while (time.time() - t_last) < timeout:
            ready = dict(self.poller.poll())
            if ready.get(self.socket):
                topic, _ = self.socket.recv_multipart()
                if topic == 'hello':
                    # Signal that we've connected and we're ready to recieve data
                    control_socket.send(b'')
                    control_socket.recv()
                    break

        assert (time.time() - t_last) < timeout, \
            "Timed out before recieving a hello topic message from the publisher."

        del control_socket
        self.socket.setsockopt(zmq.UNSUBSCRIBE, 'hello')



    def _run(self):
        self.logger.debug(self.cmd)
        p = subprocess.Popen(self.cmd, env=self._env, stdout=subprocess.PIPE,
                             stderr=subprocess.PIPE)

        # This function negotiates the late joiner problem
        self._connect()

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
