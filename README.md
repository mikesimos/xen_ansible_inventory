# Description
XEN Ansible Inventory is dynamic inventory script for listing XenServer
virtual machines. Its configurable via its ini file, or command line 
arguments.

# Installation

###### install prerequisites:
``
pip install -r requirements.txt
``

###### Clone xen_ansible_inventory at your IT Automation server:
``git clone https://github.com/mikeSimos/xen_ansible_inventory.git``

###### Configure xen_inventory.ini file accordingly.
#

# Usage
Example usage:
``
$ ansible all -i xen_inventory.py -m ping
``

# Requirements
XenServer>=6.5