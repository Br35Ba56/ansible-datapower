#!/usr/bin/python

# Copyright: (c) 2020, Anthony Schneider tonyschndr@gmail.com
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

DOCUMENTATION = r'''
---
module: action

short_description: Execute actions on a DataPower Application Domain.

version_added: "1.0.0"

description: Execute actions on a DataPower Application Domain.
    Actions are dependent on platform, domain, and or firmware version.
    Actions available include but are not limited to quiesce, save config, reboot.
    Please use export_domains, import_domains, export_objects, load_config modules for 
    Export / Import / LoadConfiguration actions.

options:
    domain:
        description: Domain to execute action on.
        required: true
        type: str
    action:
        description: The action to be performed
        required: true
        type: str
        aliases: 
          - name
    parameters:
        description: parameters, if any, that the action requires
        required: false
        type: dict

author: 
- Anthony Schneider (@br35ba56)
'''

EXAMPLES = r'''
- name: Save a domains configuration
  community.datapower.action:
    domain: default
    action: SaveConfig

- name: Quiesce DP prior to change
  community.datapower.action:
    domain: default
    action: QuiesceDP
    parameters:
      timeout: 60

- name: UnQuiesce DP prior to change
  community.datapower.action:
    domain: default
    action: UnquiesceDP
'''

RETURN = r'''
request:
    description: The request that was sent to DataPower
    type: dict
    returned: always
    sample: {
        "body": {
            "UnquiesceDP": {}
        },
        "method": "POST",
        "path": "/mgmt/actionqueue/default"
    }

response:
    description: The response from DataPower
    type: dict
    returned: on success
    sample: {
        "_links": {
            "self": {
                "href": "/mgmt/actionqueue/default/pending/UnquiesceDP-20201231T105919Z-12"
            }
        },
        "status": "completed"
    }
'''

from ansible.module_utils._text import to_text
from ansible.module_utils.connection import ConnectionError, Connection
from ansible.module_utils.basic import AnsibleModule

from ansible_collections.community.datapower.plugins.module_utils.datapower.requests import (
    ActionQueueRequest
)

from ansible.utils.display import Display

display = Display()

# Exlude actions here that have a module to perform them.
excluded_actions = {
    'Export' : [ 
        'export_domains',
        'export_objects'
    ], 
    'Import' : [
        'import_domains',
        'load_objects'
    ], 
    'LoadConfiguration' : [
        'load_objects'
    ]
}

def run_module():
    module_args = dict(
        domain = dict(type='str', required=True),
        action = dict(type='str', required=True, aliases=['name']),
        parameters = dict(type='dict', required=False)
    )
    
    module = AnsibleModule(
        argument_spec=module_args,
        supports_check_mode=False
    )
    connection = Connection(module._socket_path)
    result = {}
    domain = module.params.get('domain')
    action = module.params.get('action')

    if action in excluded_actions:
        mods = ', '.join(excluded_actions[action])
        warning_message = 'The action \'' + action + '\' has a module(s) that specifically target these actions, please see modules ' + mods
        module.warn(warning_message)
        module.fail_json(msg=warning_message, **result)

    parameters = module.params.get('parameters')
    dp_req = ActionQueueRequest(connection, domain, action, parameters)

    try:
        response = dp_req.post()
    except ConnectionError as e:
        response = to_text(e)
        result['changed'] = False
        module.fail_json(msg=response, **result)

    
    result['response'] = response
    result['request'] = {'path':dp_req.path, 'method': dp_req.method, 'body': dp_req.body}
    result['changed'] = True
    module.exit_json(**result)


def main():
    run_module()


if __name__ == '__main__':
    main()