import unittest
import inventory_test
import playbook_test

def test_suite():
    loader = unittest.TestLoader()

    suite = loader.loadTestsFromModule(inventory_test)
    suite.addTests(loader.loadTestsFromModule(playbook_test))

    return suite
