#!/usr/bin/python3

# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
from __future__ import (absolute_import, division, print_function)
from ansible.module_utils.basic import AnsibleModule
import os
import re
import shutil
__metaclass__ = type

DOCUMENTATION = r'''
---
module: filter_tests_list

short_description: Filter a tests list by allow/block tests lists

version_added: "1.0.0"

description: Get a tests list input file and filter the list by allow/block tests lists.

options:
    input_tests_file:
        description: A path of the tests list file to contain the filter on.
        required: true
        type: str
    output_file:
        description: A path of the file to output the filtered tests list.
        required: true
        type: str
    allowlist_file:
        description: A path of the allowed tests list to be used as the filter.
                     Note that regular expressions are supported.
        required: false
        type: str
    blocklist_file:
        description: A path of the blocked tests list to be used as the filter.
                     Note that regular expressions are supported.
        required: false
        type: str
'''

EXAMPLES = r'''
- name: Prepare a tests list with the allowed tests only
  shiftstack.tools.filter_tests_list:
    input_tests_file: "input_tests_path"
    allowlist_file: "allowlist_path"
    output_file: "tests_to_run_path"
'''

RETURN = r'''
input_tests_file:
    description: A path of the tests list file to contain the filter on.
    type: str
    returned: When a filter is applied
output_file:
    description: A path of the file to output the filtered tests list.
    type: str
    returned: When a filter is applied
filter_type:
    description: The type of filter applied.
    type: str
    returned: When a filter is applied
filter_tests_file:
    description: A path of the tests list file that used as a filter.
    type: str
    returned: When a filter is applied
messages:
    description: A list of logs and messages.
    type: list
    returned: Always
'''


def escape_special_characters(string):
    """Escape special characters in the given string.

    This function is needed when using the `re` functions to match a string
    containing special characters.

    Args:
        string (str): The string to escape.

    Returns:
        str: The escaped string.
    """

    translations = {
        '[': r'\[',
        ']': r'\]',
        '(': r'\(',
        ')': r'\)',
        '-': r'\-',
    }

    # create a translation table from the dictionary
    translation_table = str.maketrans(translations)
    # escape the special characters in the string.
    return string.translate(translation_table)


def normalize_test_line(line):
    """Normalize a tests-list / allow|block list line for matching.

    - Strip whitespace/newlines
    - Strip optional surrounding double quotes (legacy dry-run / convert_yaml
      wrap patterns as ``".*[lb].*"`` while OTE ``list -o names`` is unquoted)
    - Drop OTE/klog noise lines that land in list output (``I0810 ...``)
    """
    s = line.strip()
    if not s:
        return None
    # klog-style lines mixed into OTE list stdout
    if re.match(r'I\d{4}\s', s) or 'test_context.go:' in s:
        return None
    if len(s) >= 2 and s[0] == '"' and s[-1] == '"':
        s = s[1:-1].strip()
    return s or None


def run_module():
    # define the AnsibleModule object with the available
    # arguments/parameters a user can pass to the module
    module = AnsibleModule(
        argument_spec=dict(
            input_tests_file=dict(type='str', required=True),
            allowlist_file=dict(type='str', required=False),
            blocklist_file=dict(type='str', required=False),
            output_file=dict(type='str', required=True),
        )
    )

    # parse the parameters
    input_tests_file = os.path.expanduser(module.params['input_tests_file'])
    allowlist_file = os.path.expanduser(module.params['allowlist_file'])
    blocklist_file = os.path.expanduser(module.params['blocklist_file'])
    output_file = os.path.expanduser(module.params['output_file'])

    # seed the result dict in the object
    result = dict(
        changed=False,
        input_tests_file='',
        filter_type='',
        filter_tests_file='',
        output_test_file='',
        messages=[]
    )

    try:
        with open(input_tests_file, 'r') as f:
            # Preserve original lines for output, keyed by normalized name.
            input_tests_raw = [line for line in f]
    except IOError:
        module.fail_json(msg="Error opening the input tests file")

    input_tests = []
    for line in input_tests_raw:
        normalized = normalize_test_line(line)
        if normalized is not None:
            input_tests.append((normalized, line if line.endswith('\n') else line + '\n'))

    if allowlist_file and blocklist_file:
        module.fail_json(msg="parameters are mutually exclusive: "
                         "allowlist_file|blocklist_file", **result)

    elif allowlist_file:
        tests_to_run = []

        try:
            with open(allowlist_file, 'r') as f:
                allowlist = [line for line in f]
        except IOError:
            module.fail_json(msg="Error opening the allowlist file")

        for allowlist_test in allowlist:
            allow_norm = normalize_test_line(allowlist_test)
            if allow_norm is None:
                continue
            allowlist_test_in_input_tests = False
            escaped_allow_test = escape_special_characters(allow_norm)

            for test_norm, test_raw in input_tests:
                if re.fullmatch(escaped_allow_test, test_norm):
                    tests_to_run.append(test_raw)
                    allowlist_test_in_input_tests = True

            if not allowlist_test_in_input_tests:
                module.fail_json(msg="Error: Found a test that exists in {} but not in {} -"
                                 " '{}'".format(allowlist_file,
                                                input_tests_file,
                                                allowlist_test), **result)

        try:
            with open(output_file, 'w') as f:
                f.writelines(tests_to_run)
        except IOError:
            module.fail_json(msg="Error writing to output file")

        result['filter_type'] = 'allowlist'
        result['filter_tests_file'] = allowlist_file
        result['changed'] = True

    elif blocklist_file:
        try:
            with open(blocklist_file, 'r') as f:
                blocklist = [line for line in f]
        except IOError:
            module.fail_json(msg="Error opening the blocklist file")

        blocklist_norms = []
        for blocklist_test in blocklist:
            block_norm = normalize_test_line(blocklist_test)
            if block_norm is not None:
                blocklist_norms.append((block_norm, blocklist_test))

        # initialize lists for tests
        tests_to_run = []
        blocked_tests = []
        unused_blocklist_tests = []

        # iterate over the list of tests and set the tests to run
        for test_norm, test_raw in input_tests:
            test_in_blocklist = False

            for block_norm, _block_raw in blocklist_norms:
                escaped_block_test = escape_special_characters(block_norm)
                if re.fullmatch(escaped_block_test, test_norm):
                    test_in_blocklist = True
                    break

            if test_in_blocklist:
                blocked_tests.append(test_raw)
            else:
                tests_to_run.append(test_raw)

        # set the unused blocklist tests
        for block_norm, block_raw in blocklist_norms:
            escaped_block_test = escape_special_characters(block_norm)
            if not any(re.fullmatch(escaped_block_test, test_norm)
                       for test_norm, _ in input_tests):
                unused_blocklist_tests.append(block_raw)
        if unused_blocklist_tests:
            module.warn("Warning! Some tests in the blocklist were not used")
            result['unused_blocklist_tests'] = unused_blocklist_tests

        blocked_output_file = input_tests_file + ".blocked_tests"
        try:
            with open(blocked_output_file, 'w') as f:
                f.writelines(blocked_tests)
        except IOError:
            module.fail_json(
                msg="Error writing to {}".format(blocked_output_file))
        result['messages'].append(
            "The list of blocked tests has been saved at '{}'".format(blocked_output_file))

        try:
            with open(output_file, 'w') as f:
                f.writelines(tests_to_run)
        except IOError:
            module.fail_json(msg="Error writing to output file")

        result['filter_type'] = 'blocklist'
        result['filter_tests_file'] = blocklist_file
        result['changed'] = True

    else:
        # Drop klog noise even when no allow/block filter is applied (OTE list).
        try:
            with open(output_file, 'w') as f:
                for _test_norm, test_raw in input_tests:
                    f.write(test_raw)
        except IOError:
            module.fail_json(msg="Error writing to output file")

        result['filter_type'] = 'no filter applied'
        result['changed'] = True

    # in the event of a successful module execution
    if result['changed']:
        result['input_tests_file'] = input_tests_file
        result['output_test_file'] = output_file
    module.exit_json(**result)


def main():
    run_module()


if __name__ == '__main__':
    main()
