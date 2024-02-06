#!/usr/bin/python

# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
from __future__ import (absolute_import, division, print_function)
from ansible.module_utils.basic import AnsibleModule
import re
__metaclass__ = type

DOCUMENTATION = r'''
---
module: list_filter

short_description: Filter a list based on matching regular expression strings

version_added: "1.0.0"

description: Filter a list of items based on a list of patterns to use for filtering.

author: Itay Matza

options:
    list:
        description: The original list to filter.
        required: true
        type: list
    filter_type:
        description: The type of filter to apply. Can be either 'match' or 'notmatch'.
        required: true
        type: str
    filter_list:
        description: The list of strings to match or not match.
                     Note that regular expressions are supported.
        required: true
        type: list
'''

EXAMPLES = r'''
- name: Make a list with items starting with 'collect-profiles' only
  shiftstack.tools.list_filter:
    list: ['olm-operator-76b789c8d4-n8k4h', 'collect-profiles-27861660-6mz7r']
    filter_type: match
    filter_list: ['^collect-profiles.*']

- name: Make a list without the items starting with 'collect-profiles'
  shiftstack.tools.list_filter:
    list: ['olm-operator-76b789c8d4-n8k4h', 'collect-profiles-27861660-6mz7r']
    filter_type: notmatch
    filter_list: ['^collect-profiles.*']
'''

RETURN = r'''
original_list:
    description: The original list to filter.
    type: list
    returned: always
filter_type:
    description: The type of filter to apply. Can be either 'match' or 'notmatch'.
    type: str
    returned: always
filter_list:
    description: The list of strings to match or not match.
    type: list
    returned: always
filtered_list:
    description: The new list containing only the items from the original
                 list that match or do not match the strings in the filter list.
    type: list
    returned: always
'''


def _filter_list(original_list: list, filter_type: str, filter_list: list) -> list:
    new_list = []

    if filter_type == 'match':
        for item in original_list:
            for pattern in filter_list:
                if re.fullmatch(pattern, item):
                    new_list.append(item)
                    break

    elif filter_type == 'notmatch':
        for item in original_list:
            match = False
            for pattern in filter_list:
                if re.fullmatch(pattern, item):
                    match = True
                    break
            if not match:
                new_list.append(item)

    return new_list


def run_module():
    # define the module's argument specification
    module_args = dict(
        list=dict(type='list', required=True),
        filter_type=dict(type='str', required=True,
                         choices=['match', 'notmatch']),
        filter_list=dict(type='list', required=True)
    )

    # create the ansible module instance with the available
    # arguments/parameters a user can pass to the module
    module = AnsibleModule(argument_spec=module_args, supports_check_mode=True)

    # pars the parameters
    original_list = module.params['list']
    filter_type = module.params['filter_type']
    filter_list = module.params['filter_list']

    # seed the result dict in the object
    result = dict(
        changed=False,
        original_list=original_list,
        filter_type=filter_type,
        filter_list=filter_list,
        filtered_list=[]
    )

    # Filter the original list
    result['filtered_list'] = _filter_list(
        original_list, filter_type, filter_list)

    # Return the result
    module.exit_json(**result)


def main():
    run_module()


if __name__ == '__main__':
    main()
