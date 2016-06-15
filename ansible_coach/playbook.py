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
        self.env = env

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
            value = func(self, option)

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


    ############
    ## Option Functions
    ####

#     def _get_inventory_path(self, option):
#         if self._inventory_path is None:
#             if isinstance(self.inventory, basestring):
#                 self._inventory_path = self.inventory
#             elif isinstance(self.inventory, AnsibleInventory):
#                 _, self._inventory_path  = tempfile.mkstemp()
#
#         return self._inventory_path

    def _tags_as_csv(self, option):
        return ",".join(self.tags) if self.tags else None

    # option will be one of ({ '-v', '-vv', '-vvv', '-vvvv'})
    # If the option is equal to the objects verbosity level (e.g.
    # 1, 2, 3, 4) then return "" so cmd includes the option (without
    # a value).  Otherwise return None indicating that this is not
    # an option to include in cmd.
    def _ansible_log_level(self, option):
        return "" if option.count("v") == self.verbosity else None




# Options defines a mapping between a command line option to ansible-playbook
# and a function that will produce the correct value for that option
Playbook.options = [
    ("-i",  lambda s, o: s.inventory_path),
    ("-t", Playbook._tags_as_csv),
    ("-v", Playbook._ansible_log_level),
    ("-vv", Playbook._ansible_log_level ),
    ("-vvv", Playbook._ansible_log_level),
    ("-vvvv", Playbook._ansible_log_level)
]
