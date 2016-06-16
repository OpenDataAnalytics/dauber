import os
import sys
import subprocess
import logging
import tempfile
import json
import select

from inventory import AnsibleInventory

class Playbook(object):

    def __init__(self, playbook, inventory, env=None, logger=None):

        if logger is None:
            logging.basicConfig()
            self.logger = logging.getLogger(self.__class__.__name__)


        self.playbook = playbook
        self.inventory = inventory
        self._env = {}
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
        p = subprocess.Popen(self.cmd, env=self.env, stdout=subprocess.PIPE,
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
            if isinstance(self.inventory, AnsibleInventory):
                self.inventory.to_file(self.inventory_path)

            return self._run()

        finally:
            if isinstance(self.inventory, AnsibleInventory):
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
            elif isinstance(self.inventory, AnsibleInventory):
                _, self._inventory_path  = tempfile.mkstemp()

        return self._inventory_path


    def add_extra_vars(self, extra_vars):
        if isinstance(extra_vars, basestring) or isinstance(extra_vars, dict):
            self._extra_vars.append(extra_vars)
        else:
            self.logger.warn("Extra_vars must be a file path or "
                             "dict of values - doing nothing.")

    ############
    ## Option Generators
    ####

    def _tags_as_csv(self, option):
        yield ",".join(self.tags) if self.tags else None

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
