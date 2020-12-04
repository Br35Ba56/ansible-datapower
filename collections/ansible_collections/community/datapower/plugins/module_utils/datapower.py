from __future__ import absolute_import, division, print_function

__metaclass__ = type

#from urllib.parse import quote
import time
from ansible.module_utils._text import to_text
from ansible.module_utils.six.moves.urllib.parse import urlencode
from ansible.module_utils.connection import Connection, ConnectionError
from ansible.module_utils._text import to_text
from ansible_collections.community.datapower.plugins.module_utils import (
    actionqueue,
    filestore,
    config,
)
MGMT_CONFIG_BASE_WITH_OBJECT_CLASS_URI = '/mgmt/config/{0}/{1}' 
MGMT_CONFIG_WITH_NAME_URI = '/mgmt/config/{0}/{1}/{2}'
MGMT_CONFIG_WITH_FIELD_URI = '/mgmt/config/{0}/{1}/{2}/{3}'
ACTION_QUEUE_URI = '/mgmt/actionqueue/{0}'
FILESTORE_URI_PUT = '/mgmt/filestore/{0}/{1}/{2}'
FILESTORE_URI_POST = '/mgmt/filestore/{0}/{1}'

# Define the keys that get returned to the modules.  
# REQUEST_DETAILS_KEY is helps for debugging.
RESPONSE_KEY = 'response'
REQUEST_DETAILS_KEY = 'request'

class DPRequest:

    def __init__(self, module, **kwargs):
        if module:
            self.module = module
            for k, v in module.params.items():
                setattr(self, k, v)
        else:
            for k, v in kwargs.items():
                setattr(self, k, v)
        if hasattr(module, 'check_mode'):
            self.check_mode = module.check_mode
        self.connection = Connection(module._socket_path)

    def _process_request(self, method, path, body):
        result = {}
        # If the payload is being generated and modified from a get request from an earlier task,
        #  you will probably have these keys in the payload.
        # For convenience remove these so its a valid payload being sent back to DataPower REST Interface
        _scrub(body, '_links')
        _scrub(body, 'href')
        _scrub(body, 'state')
        try:
            result[RESPONSE_KEY] = self.connection.send_request(body, path, method)
        except ConnectionError:
            raise
        return result

    def send_request(self):
        try:
            if hasattr(self, 'body'):
                return self._process_request(self.method, self.path, self.body)
            else:
                return self._process_request(self.method, self.path, None)
        except ConnectionError:
            raise


class DPManageConfigRequest(DPRequest):

    def get_class_name(self):
        if hasattr(self, 'class_name') and self.class_name is not None:
            return self.class_name
        elif hasattr(self, 'object') and self.object is not None:
            return list(self.object.keys())[0]
        else:
            return None

    # If checkmode then we are not using a request body.
    def set_body(self):
        if self.check_mode:
            self.body = None
        elif hasattr(self, 'object'):
            self.body = self.object
        else:
            self.body = None

    def get_object_name(self):
        # If there is an object name you should always find it in the value of the object_class key
        if self.name is not None:
            return self.name
        else:
            return self.object.get(
                self.get_class_name()
            ).get('name')

    def set_path(self):
        if not self.get_class_name():
            raise AttributeError('class_name field is required.')
        if hasattr(self, 'obj_field') and self.obj_field:
            self.path = MGMT_CONFIG_WITH_FIELD_URI.format(self.domain, self.class_name, self.get_object_name(), self.obj_field)
        elif hasattr(self, 'name') and self.obj_field == None:
            self.path = MGMT_CONFIG_WITH_NAME_URI.format(self.domain, self.class_name, self.get_object_name())
        else:
            self.path = MGMT_CONFIG_BASE_WITH_OBJECT_CLASS_URI.format(self.domain, self.class_name)

    # If checkmode then we are setting method to GET, if not the method passed into the function.
    def set_method(self, method):
        if self.check_mode: 
            self.method = 'GET'
        elif method == "GET" or method == "POST" or method == "PUT" or method == "DELETE":
            self.method = method
        else:
            raise ConnectionError('Method not supported, choose from GET, PUT, POST, DELETE')


class DPCreate(DPManageConfigRequest):
    def __init__(self, module):
        super(DPCreate, self).__init__(module)
        if is_valid_class(self.get_class_name()):
            self.class_name = self.get_class_name()
        self.set_path()
        self.set_method('POST')
        self.set_body()
    

class DPModify(DPManageConfigRequest):
    def __init__(self, module):
        super(DPModify, self).__init__(module)
        if hasattr(self, 'name') and self.name is not None:
            pass
        else:
            self.name = self.get_object_name()

        self.class_name = self.get_class_name()
        #TODO bring this into a parent class
        if not is_valid_class(self.class_name):
            raise AttributeError('Class name %s is not a valid DataPower class_name' % self.class_name)
        
        
        #    raise AttributeError('DPModify miscombination, if your targeting the object, body is all you need. \
         #   If your targeting a list property in an object, you need to pass class_name, name and obj_field')
        
        self.set_path()
        if hasattr(self, 'obj_field') and self.obj_field is not None:
            self.set_method('POST')
        else:
            self.set_method('PUT')
        self.set_body()


class DPGet(DPManageConfigRequest):
    def __init__(self, module):
        super(DPGet, self).__init__(module)
        if not is_valid_class(self.class_name):
            raise ValueError('Invalid class_name.')
        self.set_path()
        self.method = 'GET'

    def set_path(self):
        super(DPGet, self).set_path()
        opt_str = self._get_options()
        self.path = self.path + '?' + opt_str

    def _get_options(self):
        url_params = {}
        if not hasattr(self, 'state') and not hasattr(self,'recursive'):
            return ''
        if self.state:
            url_params['state'] = '1'
        if self.recursive:
            url_params['view'] = 'recursive'
            if self.depth:
                url_params['depth'] = self.depth
            else:
                url_params['depth'] = '5'
        return urlencode(url_params, doseq=0)


class DPDelete(DPManageConfigRequest):
    
    def __init__(self, module):
        super(DPDelete, self).__init__(module)
        self.set_path()
        self.set_method('DELETE')
        self.set_body()



class DPAction(DPRequest):
    def __init__(self, module):
        super(DPAction, self).__init__(module)
        self.path = ACTION_QUEUE_URI.format(self.domain)
        self.method = 'POST'


class DPUploadFile(DPRequest):
    def __init__(self, module):
        super(DPUploadFile, self).__init__(module)  
        # Always strip /
        self.dir = self.dir.rstrip('/').lstrip('/')
        if self.overwrite:
            self.method = 'PUT'
            self.path = FILESTORE_URI_PUT.format(self.domain, self.dir, self.filename)
        else:
            self.method = 'POST'
            self.path = FILESTORE_URI_POST.format(self.domain, self.dir)
       
        self.body = {
            'file': {
                'name': self.filename,
                'content': self.content
            }
        }


class DPExportList:
    def __init__(self, objects):
        for obj in objects:
            for k, v in obj.items():
                if k == 'name' or k == 'class':
                    continue
                # Need a couple strips here to accommodate for - and _ in python code.
                # Keys need to match DP REST interface.
                obj[k.replace('_', '-')] = v
                del obj[k]
        self.objects = objects
    def _get_export_list(self):
        return self.objects


class DPConfigActions(DPRequest):

    def __init__(self, module):
        super(DPConfigActions, self).__init__(module)

    def _process_request(self, method, path, body):
        result = super(DPConfigActions, self)._process_request(method, path, body)
        export_path = None
        if result.get(RESPONSE_KEY).get('_links', None):
            export_path = result.get(RESPONSE_KEY)['_links']['location']['href']
        else:
            return result
        if export_path:
            while True:
                exp_res = super(DPConfigActions, self)._process_request('GET', export_path, body=None)
                if exp_res.get(RESPONSE_KEY)['status'] == 'completed':
                    return exp_res
                time.sleep(2)
        return result


class DPExport(DPConfigActions):

    def __init__(self, module):
        super(DPExport, self).__init__(module)
        if self.body.get('Export').get('Domain') and self.body.get('Export').get('Object'):
            raise AttributeError('Domain and Object are mutually exclusive')
        if self.body.get('Export').get('Domain', None):
            list_type = 'Domain'
        elif self.body.get('Export').get('Object', None):
            list_type = 'Object'
        else: 
            list_type = 'All'
        self.path = self.get_path()
        self.method = 'POST'
        if list_type != 'All':
            dp_exports = DPExportList(
                self.body.get('Export').get(list_type)
            )._get_export_list()
            self.body['Export'][list_type] = dp_exports


    def get_path(self):
        return ACTION_QUEUE_URI.format(self.domain)


class DPLoadConfig(DPConfigActions):

    def __init__(self, module):
        super(DPLoadConfig, self).__init__(module)
        self.path = ACTION_QUEUE_URI.format(self.domain)
        self.method = 'POST'


def _scrub(obj, bad_key):
    """
    Removes specified key from the dictionary in place.
    :param obj: dict, dictionary from DataPowers get object config rest call
    :param bad_key: str, key to remove from the dictionary
    """
    if isinstance(obj, dict):
        for key in list(obj.keys()):
            if key == bad_key:
                del obj[key]
            else:
                _scrub(obj[key], bad_key)
    elif isinstance(obj, list):
        for i in reversed(range(len(obj))):
            if obj[i] == bad_key:
                del obj[i]
            else:
                _scrub(obj[i], bad_key)
    else:
        # neither a dict nor a list, do nothing
        pass


# TODO
# This is hardcoded, pinned to DataPower v 10.0.1.0.
# This could be greatly improved by having it check an AnsibleFact.
# Would need to add a fact Module that gathers valid config object types
# from GET /mgmt/config/ and store it as a fact.
def is_valid_class(class_name):
    return config.val_obj_dict['_links'].get(class_name) or False
