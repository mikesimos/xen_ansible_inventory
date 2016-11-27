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

"""
Python script for listing Xen Server Virtual Machines for Ansible inventory
"""

import atexit
from json import load, dump, dumps
from time import time
from sys import exit
from argparse import ArgumentParser
from configparser import ConfigParser
import errno
import os
import sys
import XenAPI


class XenServer:
    """
    XenServer acts as an explicit wrapper class over XenAPI XML-RPC API,
    implementing listing (list_inventory) of XenServer resident, running VMs.
    """
    def __init__(self, xen_hostname=None, xen_username='', xen_password=''):
        """
        :param str xen_hostname: The FQDN of XenServer
        :param str xen_username: A XenServer (read only) user
        :param str xen_password: XenServer user password
        """
        try:
            session = XenAPI.Session('http://{}'.format(xen_hostname))
            session.xenapi.login_with_password(xen_username, xen_password)
        except Exception as error:
            print("Could not connect to XenServer: {}".format(error))
            sys.exit(1)
        self.session = session
        atexit.register(session.xenapi.session.logout)

    def list_inventory(self):
        """
        Lists inventory of XenServer virtual machines, grouped by their network names.
        This allows a vm being reported in multiple groups (result of having multiple NICs)
        :return:
        Ansible pluggable dynamic inventory, as a Python json serializable dictionary.
        """
        try:
            all_vms = self.session.xenapi.VM.get_all()
            inventory = {"_meta": {"hostvars": {}}}

            for vm in all_vms:
                record = self.session.xenapi.VM.get_record(vm)
                if not record["is_control_domain"] and\
                   not (record["is_a_template"]):

                    for i in record['VIFs']:
                        net_ref = self.session.xenapi.VIF.get_record(i)['network']
                        network = self.session.xenapi.network.get_record(net_ref)
                        inventory.setdefault(network['name_label'], []).append(record['name_label'])

                        # xen_tools don't provide an API reporting FQDN / hostname.
                        # Thus we need to define ansible_host with the reported IP of a vm,
                        # since using a vm name, and enforcing naming conventions through XenCenter
                        #  could cause more trouble...
                        # Let's use first assigned IP.
                        ip = self.session.xenapi\
                            .VM_guest_metrics.get_record(record['guest_metrics'])\
                            .get("networks", {}).get('0/ip')
                        host_vars = {"ansible_host": ip}
                        inventory["_meta"]["hostvars"][record['name_label']] = host_vars

            return inventory
        except XenAPI.Failure as e:
            print("[Error] : " + str(e))
            exit(1)

    def list_and_save(self, cache_path):
        """
        :param  str cache_path: A path for caching inventory list data.
        :return:
        """
        data = self.list_inventory()
        with open(cache_path, 'w') as fp:
            dump(data, fp)
        return data

    def cached_inventory(self, cache_path=None, cache_ttl=3600, refresh=False):
        """
        Wrapper method implementing caching functionality over list_inventory.
        :param str cache_path: A path for caching inventory list data. Quite a necessity for large environments.
        :param int cache_ttl: Integer Inventory list data cache Time To Live. Expiration period.
        :param boolean refresh: Setting this True, triggers a cache refresh. Fresh data is fetched.
        :return:
        Returns an Ansible pluggable dynamic inventory, as a Python json serializable dictionary.
        """
        if refresh:
            return self.list_and_save(cache_path)
        else:
            if os.path.isfile(cache_path) and time() - os.stat(cache_path).st_mtime < cache_ttl:
                try:
                    with open(cache_path) as f:
                        data = load(f)
                        return data
                except (ValueError, IOError):
                    return self.list_and_save(cache_path)
            else:
                if not os.path.exists(os.path.dirname(cache_path)):
                    try:
                        if cache_path:
                            os.makedirs(os.path.dirname(cache_path))
                        else:
                            raise OSError("cache_path not defined: {}".format(cache_path))
                    # handle race condition
                    except OSError as exc:
                        if exc.errno == errno.EACCES:
                            print("{}".format(str(exc)))
                            exit(1)
                        elif exc.errno != errno.EEXIST:
                            raise
                return self.list_and_save(cache_path)


def parse_config():
    """ Parse available configuration.
    Default configuration file: xen-inventory.ini
    Configuration file path may be overridden,
    by defining an environment variable: XEN_INVENTORY_INI_PATH
    :return: (cache_path, cache_ttl, xen_host, xen_user, xen_pass)
    """
    config = ConfigParser()
    xen_default_ini_path = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'xen-inventory.ini')
    xen_ini_path = os.path.expanduser(
        os.path.expandvars(os.environ.get('XEN_INVENTORY_INI_PATH', xen_default_ini_path)))
    config.read(xen_ini_path)
    cache_path = config.get('GENERIC', 'cache_path', fallback='/tmp/ansible-xen-inventory-cache.tmp')
    cache_ttl = config.getint('GENERIC', 'cache_ttl')
    xen_host = config.get('GENERIC', 'xen_host', fallback='')
    xen_user = config.get('GENERIC', 'xen_user', fallback='')
    xen_pass = config.get('GENERIC', 'xen_pass', fallback='')

    return cache_path, cache_ttl, xen_host, xen_user, xen_pass


def get_args():
    """
    Return Command Line Arguments.
    :return: ArgumentParser instance
    """
    parser = ArgumentParser(description="Ansible XEN inventory.",
                            epilog="Example:\n"
                                   "./xen_inventory.py -l\n"
                                   "./xen_inventory.py -s <xen.server.hostname>"
                                   "-u <xen_username> -p <xen_password> -l\n")
    parser.add_argument('-s', '--hostname', help='Xen Server FQDN')
    parser.add_argument('-u', '--username', help='Xen Server username')
    parser.add_argument('-p', '--password', help='Xen Server password')
    parser.add_argument('-g', '--guest', help='Print a single guest')
    parser.add_argument('-x', '--host', help='Print a single guest')
    parser.add_argument('-r', '--reload-cache', help='Reload cache', action='store_true')
    parser.add_argument('-l', '--list', help='List all VMs', action='store_true')
    return parser.parse_args()


def main():

    # - Get command line args and config args.
    args = get_args()
    (cache_path, cache_ttl, xen_host, xen_user, xen_pass) = parse_config()

    # - Override with arg parameters if defined
    if not args.password:
        if not xen_pass:
            import getpass
            xen_pass = getpass.getpass()
        setattr(args, 'password', xen_pass)
    if not args.username:
        setattr(args, 'username', xen_user)
    if not args.hostname:
        setattr(args, 'hostname', xen_host)

    # - Perform requested operations (list, reload-cache, host/guest)
    if args.host or args.guest:
        print ('{}')
        exit(0)
    elif args.list or args.reload_cache:
        x = XenServer(args.hostname, args.username, args.password)
        data = x.cached_inventory(cache_path=cache_path, cache_ttl=cache_ttl, refresh=args.reload_cache)
        print ("{}".format(dumps(data)))
        exit(0)


if __name__ == "__main__":
    main()
