import unittest
import mock
import os
import sys
import subprocess

sys.path.insert(0, os.path.abspath('..'))

import dauber.playbook as playbook

class PlaybookTestCase(unittest.TestCase):

    def setUp(self):
        pass

    def tearDown(self):
        pass

    ###########
    ## Clustom Assertions
    #####

    # Generate an n-gram for the list (where n is equal to the length of the tuple)
    # and check to see if the tuple is in the n-gram list
    # See: http://locallyoptimal.com/blog/2013/01/20/elegant-n-gram-generation-in-python/
    def assertTupleInList(self, tup, lst):
        self.assertIn(tup, zip(*[lst[i:] for i in range(len(tup))]))

    # This function returns a closure that will call 'env' in a subprocess using
    # the playbook object's _env attribute.  It then checks to make sure the variable
    # and the value are in the subprocess' environment.  It is intended to be used as a
    # side effect in a mocked version of the playbooks _run function.
    def assertInSubprocessEnvSideEffect(self, var, value):
        def test_env(pb_obj):
            p = subprocess.Popen(['env'], env=pb_obj._env, stdout=subprocess.PIPE)
            out, err = p.communicate()

            self.assertIn("%s=%s" % (var, value), out.split("\n"))
        return test_env

    def get_playbook_path(self, f):
        return os.path.join(
            os.path.dirname(os.path.realpath(__file__)),
            "playbooks", f)

    def test_playbook_inventory_constructor_argument(self):
        p = playbook.Playbook(self.get_playbook_path("successful.yml"),
                              playbook.Inventory("localhost"))
        code = p.run()
        self.assertEquals(code, 0)

    def test_playbook_inventory_run_argument(self):
        p = playbook.Playbook(self.get_playbook_path("successful.yml"),
                              playbook.Inventory("foo"))
        code = p.run(playbook.Inventory("localhost"))
        self.assertEquals(code, 0)


    def test_playbook_logs_failure(self):
        p = playbook.Playbook(self.get_playbook_path("missing_variable.yml"))
        p.logger.error = mock.MagicMock(return_value=None)

        p.run(playbook.Inventory("localhost"))

        self.assertTrue(p.logger.error.called)

    def test_playbook_failure_code(self):
        p = playbook.Playbook(self.get_playbook_path("missing_variable.yml"))
        p.logger = mock.MagicMock(return_value=None)
        code = p.run(playbook.Inventory("localhost"))
        self.assertNotEquals(code, 0)


    ############
    ## Test prduction of playbook command list
    #####

    def test_cmd_playbook(self):
        p = playbook.Playbook("some_playbook.yml", "some_inventory")
        self.assertEquals(p.cmd[-1], "some_playbook.yml")

    def test_cmd_string_inventory(self):
        p = playbook.Playbook("some_playbook.yml", "some_inventory")
        # We use set(zip(p.cmd, p.cmd[1:])) to generate bigrams of the command
        # This ensures that we can check order of (option, value)
        self.assertTupleInList(("-i", "some_inventory"), p.cmd)

    @mock.patch("dauber.playbook.tempfile")
    def test_cmd_Inventory_inventory(self, tempfile):
        # mock out call to tempfile.mkstemp - make sure it returns known path
        tempfile.mkstemp.return_value = (None, "/tmp/temp_inventory")

        p = playbook.Playbook("some_playbook.yml", playbook.Inventory(['localhost']))
        self.assertTrue(("-i", "/tmp/temp_inventory"), p.cmd)


    def test_cmd_string_tag(self):
        p = playbook.Playbook("some_playbook.yml", "some_inventory")
        p.tags = "test_tag"
        self.assertTupleInList(("-t", "test_tag"), p.cmd)

    def test_cmd_list_tags(self):
        p = playbook.Playbook("some_playbook.yml", "some_inventory")
        p.tags = ["test_tag", "test_other_tag"]
        self.assertTupleInList(("-t", "test_tag,test_other_tag"), p.cmd)


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
        self.assertTupleInList(("-e", "@/path/to/extra_vars.yml",
                                "-e", '{"some_variable": "some_value"}'), p.cmd)


    ############
    ## Test environment variable configuration
    #####

    @mock.patch.object(playbook.Playbook, '_run', autospec=True)
    def test_env_host_key_checking(self, _run):
        _run.return_value = 0
        _run.side_effect = self.assertInSubprocessEnvSideEffect('ANSIBLE_HOST_KEY_CHECKING', "0")

        p = playbook.Playbook("some_playbook.yml", "some_inventory")
        p.set_host_key_checking(False)
        p.run()


    @mock.patch.object(playbook.Playbook, '_run', autospec=True)
    def test_env_private_key_file(self, _run):
        _run.return_value = 0
        _run.side_effect = self.assertInSubprocessEnvSideEffect('ANSIBLE_PRIVATE_KEY_FILE', "/path/to/file.pem")

        p = playbook.Playbook("some_playbook.yml", "some_inventory")
        p.set_private_key_file("/path/to/file.pem")
        p.run()


    @mock.patch.object(playbook.Playbook, '_run', autospec=True)
    def test_env_calback_plugin_dir(self, _run):
        _run.return_value = 0
        _run.side_effect = self.assertInSubprocessEnvSideEffect('ANSIBLE_CALLBACK_PLUGINS', "/path/to/callback_plugin/")

        p = playbook.Playbook("some_playbook.yml", "some_inventory")
        p.add_callback_plugin_dir("/path/to/callback_plugin/")
        p.run()


    @mock.patch.object(playbook.Playbook, '_run', autospec=True)
    def test_env_multiple_calback_plugin_dir(self, _run):
        _run.return_value = 0
        _run.side_effect = self.assertInSubprocessEnvSideEffect('ANSIBLE_CALLBACK_PLUGINS', "/path/to/other/callback_plugin/:/path/to/callback_plugin/")

        p = playbook.Playbook("some_playbook.yml", "some_inventory")
        p.add_callback_plugin_dir("/path/to/callback_plugin/")
        p.add_callback_plugin_dir("/path/to/other/callback_plugin/")
        p.run()


    @mock.patch.object(playbook.Playbook, '_run', autospec=True)
    def test_env_library_dir(self, _run):
        _run.return_value = 0
        _run.side_effect = self.assertInSubprocessEnvSideEffect('ANSIBLE_LIBRARY', "/path/to/library_dir/")

        p = playbook.Playbook("some_playbook.yml", "some_inventory")
        p.add_library_dir("/path/to/library_dir/")
        p.run()


    @mock.patch.object(playbook.Playbook, '_run', autospec=True)
    def test_env_multiple_library_dir(self, _run):
        _run.return_value = 0
        _run.side_effect = self.assertInSubprocessEnvSideEffect('ANSIBLE_LIBRARY', "/path/to/other/library_dir/:/path/to/library_dir/")

        p = playbook.Playbook("some_playbook.yml", "some_inventory")
        p.add_library_dir("/path/to/library_dir/")
        p.add_library_dir("/path/to/other/library_dir/")
        p.run()


    ############
    ## Test Inventory temporary file creation
    #####

    @mock.patch("dauber.playbook.tempfile")
    def test_create_Inventory_tempfile(self, tempfile):
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

            p = playbook.Playbook("some_playbook.yml", playbook.Inventory(['localhost']))

            p.run()

        # Once run is complete we ensure that temp_inventory no longer exists
        # i.e.,  it has been cleaned up by the run() function
        self.assertFalse(os.path.exists("/tmp/temp_inventory"))
