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

    def assertTupleInList(self, tup, lst):
        # http://locallyoptimal.com/blog/2013/01/20/elegant-n-gram-generation-in-python/
        # Generate an n-gram for the list (where n is equal to the length of the tuple)
        # and check to see if the tuple is in the n-gram list
        self.assertIn(tup, zip(*[lst[i:] for i in range(len(tup))]))

    def test_cmd_playbook(self):
        p = playbook.Playbook("some_playbook.yml", "some_inventory")
        self.assertEquals(p.cmd[-1], "some_playbook.yml")

    def test_cmd_string_inventory(self):
        p = playbook.Playbook("some_playbook.yml", "some_inventory")
        # We use set(zip(p.cmd, p.cmd[1:])) to generate bigrams of the command
        # This ensures that we can check order of (option, value)
        self.assertTupleInList(("-i", "some_inventory"), p.cmd)

    @mock.patch("ansible_coach.playbook.tempfile")
    def test_cmd_AnsibleInventory_inventory(self, tempfile):
        # mock out call to tempfile.mkstemp - make sure it returns known path
        tempfile.mkstemp.return_value = (None, "/tmp/temp_inventory")

        p = playbook.Playbook("some_playbook.yml", playbook.AnsibleInventory(['localhost']))
        self.assertTrue(("-i", "/tmp/temp_inventory"), p.cmd)


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

    def test_cmd_string_extra_vars(self):
        p = playbook.Playbook("some_playbook.yml", "some_inventory")
        p.add_extra_vars("/path/to/extra_vars.yml")
        self.assertTupleInList(("-e", "@/path/to/extra_vars.yml"), p.cmd)

    def test_cmd_dict_extra_vars(self):
        p = playbook.Playbook("some_playbook.yml", "some_inventory")
        p.add_extra_vars({
            "some_variable": "some_value"
        })
        self.assertTupleInList(("-e", '{"some_variable": "some_value"}'), p.cmd)

    def test_cmd_multiple_extra_vars(self):
        p = playbook.Playbook("some_playbook.yml", "some_inventory")
        p.add_extra_vars("/path/to/extra_vars.yml")
        p.add_extra_vars({
            "some_variable": "some_value"
        })
        self.assertTupleInList(("-e", "@/path/to/extra_vars.yml"
                                "-e", '{"some_variable": "some_value"}'), p.cmd)

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
        with mock.patch.object(playbook.Playbook, '_run', autospec=True) as _run:
            # Set a return value so we don't actually call the fuction
            _run.return_value = 0
            # set test_temp_exists as a side effect,  the playbook object will be bound to
            # pb_obj,  and self will refer to the PlaybookTestCase instance from the surrounding
            # closure. This effectively tests that the temp_inventory file exists at the time
            # we call _call_subprocess
            _run.side_effect = test_temp_exists

            p = playbook.Playbook("some_playbook.yml", playbook.AnsibleInventory(['localhost']))

            p.run()

        # Once run is complete we ensure that temp_inventory no longer exists
        # i.e.,  it has been cleaned up by the run() function
        self.assertFalse(os.path.exists("/tmp/temp_inventory"))