#
# Copyright 2015 Peter Sprygada <psprygada@ansible.com>
#
# This file is part of Ansible
#
# Ansible is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Ansible is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Ansible.  If not, see <http://www.gnu.org/licenses/>.
#
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

from ansible_collections.ansible.netcommon.plugins.action.network import ActionModule as ActionNetworkModule
from ansible.utils.display import Display

display = Display()

class ActionModule(ActionNetworkModule):


    def run(self, tmp=None, task_vars=None):
        super(ActionModule, self).run(task_vars=task_vars)
        del tmp  # tmp no longer has any effect

        module_name = self._task.action
        self._config_module = False
        persistent_connection = self._play_context.connection.split('.')[-1]

        if persistent_connection not in ('httpapi'):
            return {'failed': True, 'msg': 'Connection type %s is not valid for this module' % self._play_context.connection}
        
        
        
        module_args = self._task.args.copy()
        module_return = self._execute_module(module_name=module_name,
                                     module_args=module_args,
                                     task_vars=task_vars)
        module_return['']
        return module_return
