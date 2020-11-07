#!/usr/bin/env python

# Copyright: (c) 2020, Your Name <YourName@example.org>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

DOCUMENTATION = r'''
---
module: community.datapower.create

short_description: Use for creating objects on IBM DataPower


version_added: "1.0.0"

description: Use for creating objects on IBM DataPower, this request will fail if the object already exists, preventing you from overwriting config.

options:
    domain:
        description: Target domain
        required: True
        type: str
    object_class:
        description: DataPower objects object_class.  Valid object_cass can be determined via GET at URI /mgmt/config/
        required: true
        type: str
    body:
        description: The configuration of the object as determined from a GET request.  
            Typically you will create the object in the GUI first.  Then you can retrieve the configuration via JSON with a GET.
        required: True
        type: dict
author:
    - Anthony Schneider
'''

EXAMPLES = r'''
# Create a datapower object.  Determine object_class by ...
- name: Create certificate
  community.datapower.create_conf:
    domain: "{{ domain }}"
    body:
      CryptoCertificate:
        name: Test2
        mAdminState: enabled
        Filename: cert:///webgui-sscert.pem
        PasswordAlias: 'off'
        IgnoreExpiration: 'off'

'''

RETURN = r'''
# These are examples of possible return values, and in general should use other names for return values.
request:
    description: The request that was sent to DataPower
    type: dict
    returned: always
    sample: {
        "body": {
            "CryptoCertificate": {
                "Filename": "cert:///webgui-sscert.pem",
                "IgnoreExpiration": "off",
                "PasswordAlias": "off",
                "mAdminState": "enabled",
                "name": "Test2"
            }
        },
        "method": "POST",
        "path": "/mgmt/config/default/CryptoCertificate"
    }

response:
    description: A Dictionary representing the response returned from DataPowers Rest MGMT Interface
    type: dict
    returned: on success
    sample:  {
        "Test2": "Configuration was created.",
        "_links": {
            "doc": {
                "href": "/mgmt/docs/config/CryptoCertificate"
            },
            "location": {
                "href": "/mgmt/config/default/CryptoCertificate/Test2"
            },
            "self": {
                "href": "/mgmt/config/default/CryptoCertificate"
            }
        }
    }
'''

from ansible.module_utils.basic import AnsibleModule
from ansible_collections.community.datapower.plugins.module_utils.datapower import (
    DPCreate,
    check_for_error
)

def run_module():
    # define available arguments/parameters a user can pass to the module
    module_args = dict(
        domain=dict(type='str', required=True),
        body=dict(type='dict', required=True)
    )
    
    # seed the result dict in the object
    # we primarily care about changed and state
    # changed is if this module effectively modified the target
    # state will include any data that you want your module to pass back
    # for consumption, for example, in a subsequent task
  

    # the AnsibleModule object will be our abstraction working with Ansible
    # this includes instantiation, a couple of common attr would be the
    # args/params passed to the execution, as well as if the module
    # supports check mode
    module = AnsibleModule(
        argument_spec=module_args,
        supports_check_mode=True
    )
    
    # if the user is working with this module in only check mode we do not
    # want to make any changes to the environment, just return the current
    # state with no modifications
    if module.check_mode:
        module.exit_json(**result)

    dp_create = DPCreate(module)
    try:
        result = dp_create.send_request()
    except ConnectionError as ce:
        result = dict()
        result['changed'] = False
        module.fail_json(msg="Failed to create configuration.", **result)

    result['changed'] = True

    # in the event of a successful module execution, you will want to
    # simple AnsibleModule.exit_json(), passing the key/value results
    module.exit_json(**result)


def main():
    run_module()


if __name__ == '__main__':
    main()