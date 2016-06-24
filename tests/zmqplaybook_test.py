import unittest
import mock
import os
import sys
import subprocess
import mock

sys.path.insert(0, os.path.abspath('..'))

import dauber.zmqplaybook as playbook
from dauber import Inventory

class ZMQPlaybookTestCase(unittest.TestCase):

    def setUp(self):
        pass

    def tearDown(self):
        pass

    def get_playbook_path(self, f):
        return os.path.join(
            os.path.dirname(os.path.realpath(__file__)),
            "playbooks", f)

    def check_task_result(self, result, **kwargs):
        self.assertIn('_result', result)
        self.assertIn('_task', result)

    def check_task(self, task, **kwargs):
        self.assertIn('action', task)

    def test_v2_runner_on_ok_called(self):
        p = playbook.ZMQPlaybook(self.get_playbook_path("zmq_runner_on_ok.yml"))

        m = mock.Mock()
        p.add_hook('v2_runner_on_ok', m)
        p.run(Inventory(["localhost"]))
        self.assertTrue(m.called)


    def test_v2_runner_on_ok(self):
        p = playbook.ZMQPlaybook(self.get_playbook_path("zmq_runner_on_ok.yml"))

        p.add_hook('v2_runner_on_ok', self.check_task_result)
        p.run(Inventory(["localhost"]))


    def test_v2_runner_on_failed_called(self):
        p = playbook.ZMQPlaybook(self.get_playbook_path("zmq_runner_on_failed.yml"))
        m = mock.Mock()
        p.add_hook('v2_runner_on_failed', m)
        p.run(Inventory(["localhost"]))
        self.assertTrue(m.called)

    def test_v2_runner_on_failed_called(self):
        p = playbook.ZMQPlaybook(self.get_playbook_path("zmq_runner_on_failed.yml"))
        p.add_hook('v2_runner_on_failed', self.check_task_result)
        p.run(Inventory(["localhost"]))


    def test_v2_playbook_on_no_hosts_matched_called(self):
        p = playbook.ZMQPlaybook(self.get_playbook_path("zmq_runner_no_hosts.yml"))
        m = mock.Mock()
        p.add_hook('v2_playbook_on_no_hosts_matched', m)
        p.run(Inventory(["localhost"]))
        self.assertTrue(m.called)


    def test_v2_runner_on_skipped_called(self):
        p = playbook.ZMQPlaybook(self.get_playbook_path("zmq_runner_on_skipped.yml"))
        m = mock.Mock()
        p.add_hook('v2_runner_on_skipped', m)
        p.run(Inventory(["localhost"]))
        self.assertTrue(m.called)


    def test_v2_runner_on_skipped(self):
        p = playbook.ZMQPlaybook(self.get_playbook_path("zmq_runner_on_skipped.yml"))
        p.add_hook('v2_runner_on_skipped', self.check_task_result)
        p.run(Inventory(["localhost"]))


    def test_v2_on_any_called(self):
        p = playbook.ZMQPlaybook(self.get_playbook_path("zmq_runner_on_ok.yml"))
        m = mock.Mock()
        p.add_hook('v2_on_any', m)
        p.run(Inventory(["localhost"]))
        self.assertEquals(m.call_count, 7)


    def test_v2_playbook_on_start_called(self):
        p = playbook.ZMQPlaybook(self.get_playbook_path("zmq_runner_on_ok.yml"))
        m = mock.Mock()
        p.add_hook('v2_playbook_on_start', m)
        p.run(Inventory(["localhost"]))
        self.assertTrue(m.called)

    def test_v2_playbook_on_start_called(self):
        p = playbook.ZMQPlaybook(self.get_playbook_path("zmq_runner_on_ok.yml"))
        def test_playbook(playbook):
            self.assertIn('_entries', playbook)

        p.add_hook('v2_playbook_on_start', test_playbook)
        p.run(Inventory(["localhost"]))


    def test_v2_playbook_on_task_start_called(self):
        p = playbook.ZMQPlaybook(self.get_playbook_path("zmq_playbook_on_task_start.yml"))
        m = mock.Mock()
        p.add_hook('v2_playbook_on_task_start', m)
        p.run(Inventory(["localhost"]))
        self.assertEquals(m.call_count, 3)


    def test_v2_playbook_on_task_start(self):
        p = playbook.ZMQPlaybook(self.get_playbook_path("zmq_playbook_on_task_start.yml"))
        p.add_hook('v2_playbook_on_task_start', self.check_task)
        p.run(Inventory(["localhost"]))



    def test_v2_playbook_on_include_called(self):
        p = playbook.ZMQPlaybook(self.get_playbook_path("zmq_playbook_on_include.yml"))
        m = mock.Mock()
        p.add_hook('v2_playbook_on_include', m)
        p.run(Inventory(["localhost"]))
        self.assertTrue(m.called)


    @unittest.skip('to implement')
    def test_v2_playbook_on_include(self):
        pass


    @unittest.skip('to implement')
    def test_v2_playbook_on_stats_called(self):
        pass

    @unittest.skip('to implement')
    def test_v2_playbook_on_stats(self):
        pass





#     def test_v2_runner_on_unreachable_called(self):
#         pass
#
#
#     def test_v2_runner_on_unreachable(self):
#         pass
#
#
#
#     def test_v2_playbook_on_no_hosts_remaining_called(self):
#         pass
#
#
#
#     def test_v2_playbook_on_handler_task_start_called(self):
#         pass
#
#
#     def test_v2_playbook_on_handler_task_start(self):
#         pass
#
#
#
#     def test_v2_runner_on_item_ok_called(self):
#         pass
#
#
#     def test_v2_runner_on_item_ok(self):
#         pass
#
#
#     def test_v2_runner_on_item_failed_called(self):
#         pass
#
#
#     def test_v2_runner_on_item_failed(self):
#         pass
#
#
#     def test_v2_runner_on_item_skipped_called(self):
#         pass
#
#
#     def test_v2_runner_on_item_skipped(self):
#         pass
#
#
#
#     def test_v2_runner_on_cleanup_task_start_called(self):
#         pass
#
#
#     def test_v2_runner_on_cleanup_task_start(self):
#         pass
#
#
#     def test_v2_on_file_diff_called(self):
#         pass
#
#
#     def test_v2_on_file_diff(self):
#         pass
#
#
#
#     def test_v2_runner_retry_called(self):
#         pass
#
#
#     def test_v2_runner_retry(self):
#         pass
