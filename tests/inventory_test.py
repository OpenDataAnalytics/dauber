import unittest
import os
import sys
sys.path.insert(0, os.path.abspath('..'))

import dauber.inventory as inventory

class InventoryTestCase(unittest.TestCase):

    def setUp(self):
        pass

    def tearDown(self):
        pass

    def test_ansible_inventory_host_basic(self):
        case = 'localhost'
        h = inventory.InventoryHost(case)
        self.assertEquals(case, h.host)
        self.assertEquals(case, h.to_string())

    def test_ansible_inventory_host_basic_read_from_string(self):
        case = 'localhost'
        h = inventory.InventoryHost.from_string(case)
        self.assertEquals(case, h.host)
        self.assertEquals(case, h.to_string())

    def test_ansible_inventory_host_variables_to_string(self):
        target = 'localhost foo=bar baz=bar'
        h = inventory.InventoryHost('localhost', foo='bar', baz='bar')

        # Ensure variables have been set on host
        self.assertTrue('foo' in h.variables)
        self.assertEquals(h.variables['foo'], 'bar')
        self.assertTrue('baz' in h.variables)
        self.assertEquals(h.variables['baz'], 'bar')

        # Test to_string
        self.assertEquals(h.to_string(), target)

    def test_ansible_inventory_host_malformed_host(self):
        cases = ['localhost foo',
                 'localhost foo=',
                 'localhost foo= bar',
                 'localhost foo==bar',
                 'localhost foo = bar']
        for case in cases:
            with self.assertRaises(RuntimeError):
                inventory.InventoryHost.from_string(case)

    def test_ansible_inventory_host_equality(self):
        source = inventory.InventoryHost('localhost',
                                                foo='bar', bar='baz')
        target = inventory.InventoryHost('localhost',
                                                foo='bar', bar='baz')

        malformed1 = inventory.InventoryHost('other_host',
                                                    foo='bar', bar='baz')
        malformed2 = inventory.InventoryHost('localhost', foo='bar')

        self.assertEquals(source, target)

        self.assertNotEquals(source, malformed1)
        self.assertNotEquals(source, malformed2)

    def test_ansible_inventory_group_name(self):
        g = inventory.InventoryGroup('[foobar]')
        self.assertEquals(g.heading, '[foobar]')
        self.assertEquals(g.name, 'foobar')

    def test_ansible_inventory_group_set_name(self):
        g = inventory.InventoryGroup('[foobar]')
        g.name = 'FOOBAR'
        self.assertEquals(g.name, 'FOOBAR')
        self.assertEquals(g.heading, '[FOOBAR]')

    def test_ansible_inventory_headding_mangling(self):
        g = inventory.InventoryGroup('[foobar]')
        self.assertEquals(g.heading, '[foobar]')
        self.assertEquals(g.name, 'foobar')

        g = inventory.InventoryGroup('foobar]')
        self.assertEquals(g.heading, '[foobar]')
        self.assertEquals(g.name, 'foobar')

        g = inventory.InventoryGroup('foobar')
        self.assertEquals(g.heading, '[foobar]')
        self.assertEquals(g.name, 'foobar')

    def test_ansible_inventory_group_items(self):
        base = 'localhost foo=bar bar=baz'
        h = inventory.InventoryHost.from_string(base)

        g = inventory.InventoryGroup('[foobar]', [base])

        self.assertEquals(len(g.items), 1)
        self.assertEquals(g.items[0], h)

        g2 = inventory.InventoryGroup('[foobar]', [h])

        self.assertEquals(len(g2.items), 1)
        self.assertEquals(g.items[0], g2.items[0])

    def test_ansible_inventory_group_treat(self):
        self.assertTrue(inventory.InventoryGroup.treat('[foobar]'))
        self.assertFalse(inventory.InventoryGroup.treat(
            '[foobar:vars]'))
        self.assertFalse(inventory.InventoryGroup.treat(
            '[foobar:children]'))
        self.assertFalse(inventory.InventoryGroup.treat('foobar'))

    def test_ansible_inventory_basic(self):
        script = '''localhost
'''

        i = inventory.Inventory.from_string(script)

        self.assertEquals(len(i.global_hosts), 1)

        self.assertTrue(isinstance(i.global_hosts[0],
                                   inventory.InventoryHost))

        self.assertEquals(i.global_hosts[0].to_string(), 'localhost')

        self.assertEquals(i.to_string(), script)

    def test_ansible_inventory_with_variables(self):
        script = '''localhost foo=bar baz=bar
'''
        i = inventory.Inventory.from_string(script)
        self.assertEquals(i.to_string(), script)

    def test_ansible_inventory_with_groups(self):
        script = '''localhost foo=bar baz=bar

[some_group]
localhost foo=other
192.168.1.10

[another group]
192.168.1.10

'''
        i = inventory.Inventory.from_string(script)
        self.assertEquals(len(i.global_hosts), 1)

        self.assertEquals(i.global_hosts[0].host, 'localhost')
        self.assertTrue('foo' in i.global_hosts[0].variables)
        self.assertEquals(i.global_hosts[0].variables['foo'], 'bar')
        self.assertTrue('baz' in i.global_hosts[0].variables)
        self.assertEquals(i.global_hosts[0].variables['baz'], 'bar')

        self.assertEquals(len(i.sections), 2)
        self.assertEquals(i.sections[0].name, 'some_group')
        self.assertEquals(i.sections[0].heading, '[some_group]')

        self.assertEquals(len(i.sections[0].items), 2)

        self.assertEquals(i.sections[0].items[0].host, 'localhost')
        self.assertTrue('foo' in i.sections[0].items[0].variables)
        self.assertEquals(i.sections[0].items[0].variables['foo'], 'other')
        self.assertEquals(i.sections[0].items[1].host, '192.168.1.10')

        self.assertEquals(i.sections[1].name, 'another group')
        self.assertEquals(i.sections[1].heading, '[another group]')
        self.assertEquals(i.sections[1].items[0].host, '192.168.1.10')

        self.assertEquals(i.to_string(), script)

    def test_ansible_inventory_tempfile_context_manager(self):
        target = '''localhost foo=bar baz=bar

[some_group]
localhost foo=other
192.168.1.10

[another group]
192.168.1.10

'''
        i = inventory.Inventory.from_string(target)

        with i.to_tempfile() as path:
            self.assertTrue(os.path.exists(path))
            with open(path, 'rb') as fh:
                source = fh.read()
                self.assertEquals(source, target)

        self.assertFalse(os.path.exists(path))

    def test_ansible_inventory_as_host(self):
        source = inventory.Inventory.as_host('localhost foo=bar')
        target = inventory.InventoryHost('localhost', foo='bar')

        self.assertEquals(source, target)

        i = inventory.Inventory(['localhost foo=bar'])

        self.assertEquals(len(i.global_hosts), 1)
        self.assertEquals(source, i.global_hosts[0])

    def test_ansible_inventory_api(self):
        target = '''localhost foo=bar baz=bar

[some_group]
localhost foo=other
192.168.1.10

[another group]
192.168.1.10

'''
        i = inventory.Inventory(
            ['localhost foo=bar baz=bar'],
            sections=[
                inventory.InventoryGroup(
                    'some_group',
                    ['localhost foo=other', '192.168.1.10']
                ),
                inventory.InventoryGroup(
                    'another group',
                    ['192.168.1.10']
                )
            ]
        )

        self.assertEquals(i.to_string(), target)

    def test_ansible_inventory_to_json(self):
        source = '''localhost foo=bar baz=bar

[some_group]
localhost foo=other
192.168.1.10

[another group]
192.168.1.10

'''
        target = '{"_meta": {"hostvars": {"192.168.1.10": {}, "localhost": ' + \
                 '{"foo": "other", "baz": "bar"}}}, "some_group": ' + \
                 '["localhost", "192.168.1.10"], "another group": ' + \
                 '["192.168.1.10"]}'
        i = inventory.Inventory.from_string(source)

        self.assertEquals(i.to_json(), target)

    def test_ansible_inventory_from_json(self):
        target = '''192.168.1.10
localhost foo=other baz=bar

[some_group]
localhost
192.168.1.10

[another group]
192.168.1.10

'''
        source = '{"_meta": {"hostvars": {"192.168.1.10": {}, "localhost": ' + \
                 '{"foo": "other", "baz": "bar"}}}, "some_group": ' + \
                 '["localhost", "192.168.1.10"], "another group": ' + \
                 '["192.168.1.10"]}'
        i = inventory.Inventory.from_json(source)

        self.assertEquals(i.to_string(), target)


    def test_simple_inventory_string(self):
        target = inventory.Inventory(['localhost'])
        source = inventory.simple_inventory('localhost')

        self.assertEquals(source.to_string(), target.to_string())

    def test_simple_inventory_list(self):
        target = inventory.Inventory(['localhost', 'localhost2'])
        source = inventory.simple_inventory(['localhost', 'localhost2'])

        self.assertEquals(source.to_string(), target.to_string())

    def test_simple_inventory_dict(self):
        target = inventory.Inventory([], sections=[
            inventory.InventoryGroup('test', ['localhost', 'localhost2'])])

        source = inventory.simple_inventory(
            {"test": ["localhost", "localhost2"]})

        self.assertEquals(source.to_string(), target.to_string())

    def test_simple_inventory_string_and_dict(self):
        target = inventory.Inventory(['localhost'], sections=[
            inventory.InventoryGroup('test', ['localhost', 'localhost2'])])

        source = inventory.simple_inventory(
            'localhost',
            {"test": ["localhost", "localhost2"]})

        self.assertEquals(source.to_string(), target.to_string())

    def test_simple_inventory_list_and_dict(self):
        target = inventory.Inventory(
            ['localhost', 'localhost2'],
            sections=[
                inventory.InventoryGroup(
                    'test',
                    ['localhost', 'localhost2'])])

        source = inventory.simple_inventory(
            ['localhost', 'localhost2'],
            {"test": ["localhost", "localhost2"]})

        self.assertEquals(source.to_string(), target.to_string())
