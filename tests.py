#!/usr/bin/env python

#   This file is part of Ansible XEN Inventory.
#
#   Ansible XEN Inventory is free software: you can redistribute it and/or
#   modify it under the terms of the GNU General Public License as published by
#   the Free Software Foundation, either version 2 of the License, or (at your
#   option) any later version.
#
#   Ansible XEN Inventory is distributed in the hope that it will be useful,
#   but WITHOUT ANY WARRANTY; without even the implied warranty of
#   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
#   GNU General Public License for more details.
#   You should have received a copy of the GNU General Public License
#   along with Ansible XEN Inventory. If not, see <http://www.gnu.org/licenses/>.
#
# Authors:
# version 0.1 Michael-Angelos Simos

import unittest


class XenAnsibleTestCase(unittest.TestCase):

    def test_list_inventory(self):
        from xen_inventory import XenServer
        self.assertTrue(getattr(XenServer, 'list_inventory'))

    def test_list_and_save(self):
        from xen_inventory import XenServer
        self.assertTrue(getattr(XenServer, 'list_and_save'))

    def test_cached_inventory(self):
        from xen_inventory import XenServer
        self.assertTrue(getattr(XenServer, 'cached_inventory'))

    def test_parse_config(self):
        from xen_inventory import parse_config
        self.assertEqual(type(parse_config()), type(()))

    def test_get_args(self):
        import xen_inventory
        self.assertTrue(getattr(xen_inventory, 'get_args'))

if __name__ == '__main__':
    unittest.main()
