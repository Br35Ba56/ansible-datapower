#!/usr/bin/env python

# Copyright: (c) 2020, Anthony Schneider tonyschndr@gmail.com
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

DOCUMENTATION = r'''
---
module: community.datapower.get_conf

short_description: Use for geting objects on IBM DataPower


version_added: "1.0.0"

description: Use for getting object configuration

options:
    domain:
        description: Target domain
        required: True
        type: str
    object_class:
        description: DataPower objects object_class.  Valid Object class can be determined with a GET on URI /mgmt/config/
        required: true
        type: str
    name:
        description: Name of object as seen in DataPower
    options:
        description: Options for retrieving objects.
        required: False
        type: dict
        recursive:
            description: Get target objects referenced objects.
            required: False
            type: bool
        depth:
            description: Set the depth of the recursion.
            required: False
            type: int
            default: 7
        state:
            description: If true return state information on all returned objects.
            required: False
            type: bool
            default: False


author:
    - Anthony Schneider
'''

EXAMPLES = r'''
# Get a datapower object.  Determine object_class by ...
- name: Get the cert Test2
  community.datapower.get_conf:
    domain: "{{ domain }}"
    class_name: CryptoCertificate
    name: Test2
- name: Get the valcred and referenced objects recursively, return state of all objects as well.
  community.datapower.get_conf:
    domain: "{{ domain }}"
    class_name: CryptoValCred
    name: valcred
    recursive: True
    state: True
    depth: 3
- name: Get all valcreds
  community.datapower.get_conf:
    domain: "{{ domain }}"
    class_name: CryptoValCred
'''

RETURN = r'''
# These are examples of possible return values, and in general should use other names for return values.
request:
    description: The request that was sent to DataPower
    type: dict
    returned: always
    sample: {
        "body": null,
        "method": "GET",
        "path": "/mgmt/config/default/CryptoValCred?"
    }

response:
    description: A Dictionary representing the response returned from DataPowers Rest MGMT Interface
    type: dict
    returned: on success
    sample:  {
        "CryptoCertificate": {
            "Filename": "cert:///webgui-sscert.pem",
            "IgnoreExpiration": "off",
            "PasswordAlias": "off",
            "mAdminState": "disabled",
            "name": "Test2"
        },
        "_links": {
            "doc": {
                "href": "/mgmt/docs/config/CryptoCertificate"
            },
            "self": {
                "href": "/mgmt/config/default/CryptoCertificate/Test2"
            }
        }
    }
'''

from ansible.module_utils._text import to_text
from ansible.module_utils.connection import ConnectionError
from ansible.module_utils.basic import AnsibleModule
from ansible_collections.community.datapower.plugins.module_utils.datapower.dp_obj import (
    DPConfigObject
)

def run_module():
    module_args = dict(
        domain=dict(type='str', required=True),
        class_name=dict(type='str', required=True),
        object_name=dict(type='str', required=False),
        object_field=dict(type='str', required=False),
        recursive=dict(type='bool', required=False),
        depth=dict(type='int', required=False),
        state=dict(type='str', choices=['present', 'absent'], required=True)
    )

    mutually_exclusive = [
        ['obj_field', 'recursive'],
    ]
    
    module = AnsibleModule(
        argument_spec=module_args,
        supports_check_mode=False,
        mutually_exclusive=mutually_exclusive
    )
    
    dp_obj = DPConfigObject(**module.params)
    
    
    result = {}
    result['dp_obj'] = vars(dp_obj)

    module.exit_json(**result)


def main():
    run_module()


if __name__ == '__main__':
    main()