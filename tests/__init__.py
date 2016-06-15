import unittest
import ansible_inventory_test

def test_suite():
    loader = unittest.TestLoader()
    suite = loader.loadTestsFromModule(ansible_inventory_test)

    return suite
