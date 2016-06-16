###############################################################################
#  Copyright 2016 Kitware Inc.
#
#  Licensed under the Apache License, Version 2.0 ( the "License" );
#  you may not use this file except in compliance with the License.
#  You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
#  Unless required by applicable law or agreed to in writing, software
#  distributed under the License is distributed on an "AS IS" BASIS,
#  WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#  See the License for the specific language governing permissions and
#  limitations under the License.
###############################################################################

import os
import sys
import subprocess
import logging
import tempfile
import json
import select

from inventory import Inventory

class Playbook(object):

    def __init__(self, playbook, inventory, env=None, logger=None):

        if logger is None:
            logging.basicConfig()
            self.logger = logging.getLogger(self.__class__.__name__)


        self.playbook = playbook
        self.inventory = inventory

        self._env = os.environ.copy()
        self._env.update(env if env is not None else {})

        self._extra_vars = []

        self.tags = []
        self.verbosity = 1

        self.ansible_playbook_bin = "ansible-playbook"

        with open(os.devnull, 'w') as fnull:
            if subprocess.call(["which", self.ansible_playbook_bin],
                               stdout=fnull, stderr=fnull) != 0:
                self.logger.error("Could not locate '{}' script"
                                  .format(self.ansible_playbook_bin))

        self._inventory_path = None

    def _run(self):
        p = subprocess.Popen(self.cmd, env=self._env, stdout=subprocess.PIPE,
                             stderr=subprocess.PIPE)
        while True:
            reads = [p.stdout.fileno(), p.stderr.fileno()]
            ret = select.select(reads, [], [])

            for fd in ret[0]:
                if fd == p.stdout.fileno():
                    self.logger.info(p.stdout.readline())
                if fd == p.stderr.fileno():
                    self.logger.error(p.stderr.readline())

                if p.poll() is not None:
                    return p.wait()


    def run(self):
        try:
            if isinstance(self.inventory, Inventory):
                self.inventory.to_file(self.inventory_path)

            return self._run()

        finally:
            if isinstance(self.inventory, Inventory):
                try:
                    os.remove(self.inventory_path)
                except FileNotFoundError:
                    pass

                self._inventory_path = None


    def __call__(self):
        return self.run()

    @property
    def cmd(self):
        cmd = [self.ansible_playbook_bin]
        for option, func in self.options:
            # Func must be a generator so we can support multiple options
            # (e.g.  ansible-playbook ... -e '{"foo": "bar"}' -e @/path/to/file ...)
            for value in func(self, option):
                # If our function returns "" then assume it is an option with no value
                # (e.g.  -vvvv)
                if value is "":
                    cmd.append(option)

                # otherwise only add option/value if value is not None
                elif value is not None:
                    cmd.extend( [option, value] )

        cmd.append(self.playbook)

        return cmd


    @property
    def inventory_path(self):
        if self._inventory_path is None:
            if isinstance(self.inventory, basestring):
                self._inventory_path = self.inventory
            elif isinstance(self.inventory, Inventory):
                _, self._inventory_path  = tempfile.mkstemp()

        return self._inventory_path


    def add_extra_vars(self, extra_vars):
        if isinstance(extra_vars, basestring) or isinstance(extra_vars, dict):
            self._extra_vars.append(extra_vars)
        else:
            self.logger.warn("Extra_vars must be a file path or "
                             "dict of values - doing nothing.")

    ############
    ## Environment Variable config support
    ####

    def set_host_key_checking(self, to=False):
        self._env['ANSIBLE_HOST_KEY_CHECKING'] = "1" if to else "0"

    def set_private_key_file(self, to):
        self._env['ANSIBLE_PRIVATE_KEY_FILE'] = to

    def set_ssh_args(self, to):
        if isinstance(self, to, basestring):
            self._env['ANSIBLE_SSH_ARGS'] = to
        else:
            self._env['ANSIBLE_SSH_ARGS'] = ' '.join(to)

    def _prepend_path_to_var(self, path, env_var):
        try:
            plugin_dirs = self._env[env_var].split(":")
        except KeyError:
            plugin_dirs = []

        self._env[env_var] = ":".join([path] + plugin_dirs)

    def add_callback_plugin_dir(self, path):
        self._prepend_path_to_var(path, "ANSIBLE_CALLBACK_PLUGINS")

    def add_library_dir(self, path):
        self._prepend_path_to_var(path, "ANSIBLE_LIBRARY")


    ############
    ## Option Generators
    ####

    def _tags_as_csv(self, option):
        yield ",".join(
            [self.tags] if isinstance(self.tags, basestring) else self.tags) \
            if self.tags else None

    # option will be one of ({ '-v', '-vv', '-vvv', '-vvvv'})
    # If the option is equal to the objects verbosity level (e.g.
    # 1, 2, 3, 4) then return "" so cmd includes the option (without
    # a value).  Otherwise return None indicating that this is not
    # an option to include in cmd.
    def _ansible_log_level(self, option):
        yield "" if option.count("v") == self.verbosity else None


    def _extra_vars(self, option):
        for extra_vars in self._extra_vars:
            if isinstance(extra_vars, basestring):
                yield "@" + extra_vars
            elif isinstance(extra_vars, dict):
                yield json.dumps(extra_vars)

    def _inventory_path(self, option):
        yield self.inventory_path

# Options defines a mapping between a command line option to ansible-playbook
# and a function that will produce the correct value for that option
Playbook.options = [
    ("-i",  Playbook._inventory_path),
    ("-e", Playbook._extra_vars),
    ("-t", Playbook._tags_as_csv),
    ("-v", Playbook._ansible_log_level),
    ("-vv", Playbook._ansible_log_level ),
    ("-vvv", Playbook._ansible_log_level),
    ("-vvvv", Playbook._ansible_log_level)
]
