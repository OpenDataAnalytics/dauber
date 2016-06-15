import unittest
import mock
import os
import sys
sys.path.insert(0, os.path.abspath('..'))

import ansible_coach.playbook as playbook

class PlaybookTestCase(unittest.TestCase):

    def setUp(self):
        pass

    def tearDown(self):
        pass

    def test_cmd_playbook(self):
        p = playbook.Playbook("some_playbook.yml", "some_inventory")
        self.assertEquals(p.cmd[-1], "some_playbook.yml")

    def test_cmd_string_inventory(self):
        p = playbook.Playbook("some_playbook.yml", "some_inventory")
        # We use set(zip(p.cmd, p.cmd[1:])) to generate bigrams of the command
        # This ensures that we can check order of (option, value)
        self.assertTrue(("-i", "some_inventory") in set(zip(p.cmd, p.cmd[1:])))

    @mock.patch("ansible_coach.playbook.tempfile")
    def test_cmd_AnsibleInventory_inventory(self, tempfile):
        # mock out call to tempfile.mkstemp - make sure it returns known path
        tempfile.mkstemp.return_value = (None, "/tmp/temp_inventory")

        p = playbook.Playbook("some_playbook.yml", playbook.AnsibleInventory(['localhost']))
        self.assertTrue(("-i", "/tmp/temp_inventory") in set(zip(p.cmd, p.cmd[1:])))


    def test_cmd_default_verbosity(self):
        p = playbook.Playbook("some_playbook.yml", "some_inventory")
        self.assertTrue("-v" in p.cmd)
        self.assertTrue("-vv" not in p.cmd)
        self.assertTrue("-vvv" not in p.cmd)
        self.assertTrue("-vvvv" not in p.cmd)


    def test_cmd_other_verbosity_levels(self):
        p = playbook.Playbook("some_playbook.yml", "some_inventory")
        p.verbosity = 0
        self.assertTrue("-v" not in p.cmd)
        self.assertTrue("-vv" not in p.cmd)
        self.assertTrue("-vvv" not in p.cmd)
        self.assertTrue("-vvvv" not in p.cmd)

        p.verbosity = 2
        self.assertTrue("-vv" in p.cmd)

        p.verbosity = 3
        self.assertTrue("-vvv" in p.cmd)

        p.verbosity = 4
        self.assertTrue("-vvvv" in p.cmd)

    @mock.patch("ansible_coach.playbook.tempfile")
    def test_create_AnsibleInventory_tempfile(self, tempfile):
        # Mock out mkstemp's value so we have a known location for the inventory file
        # TODO: this should be using package_resources to create this file in a local temporary
        #       test directory instead of just in '/tmp/'
        tempfile.mkstemp.return_value = (None, "/tmp/temp_inventory")

        # will use this as a side effect of _call_subprocess
        def test_temp_exists(pb_obj):
            self.assertTrue(os.path.exists("/tmp/temp_inventory"))

        # mock out _call_subprocess on Playbook - we don't want to actually call subprocess
        with mock.patch.object(playbook.Playbook, '_call_subprocess', autospec=True) as cs:
            # Set a return value so we don't actually call the fuction
            cs.return_value = 0
            # set test_temp_exists as a side effect,  the playbook object will be bound to
            # pb_obj,  and self will refer to the PlaybookTestCase instance from the surrounding
            # closure. This effectively tests that the temp_inventory file exists at the time
            # we call _call_subprocess
            cs.side_effect = test_temp_exists

            p = playbook.Playbook("some_playbook.yml", playbook.AnsibleInventory(['localhost']))

            p.run()

        # Once run is complete we ensure that temp_inventory no longer exists
        # i.e.,  it has been cleaned up by the run() function
        self.assertFalse(os.path.exists("/tmp/temp_inventory"))
