#!/usr/bin/python

# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
from ansible.module_utils.basic import AnsibleModule
import xml.etree.ElementTree as ET
__metaclass__ = type

DOCUMENTATION = r'''
---
module: parse_junit_test_results

short_description: Parse JUnit test results from an XML report.

version_added: "1.0.0"

description:
  - This Ansible module parses a JUnit XML report and counts the number of different test results, such as passed, failed, error, and disabled tests.

author: Itay Matza

options:
  xml_report:
    description:
      - Path to the JUnit XML report file.
    required: true
    type: str
'''

EXAMPLES = r'''
- name: Parse JUnit Test Results
  hosts: localhost
  tasks:
    - name: Parse test results in JUnit XML report
      parse_junit_test_results:
        xml_report: path/to/your/junit-report.xml
      register: test_results

    - name: Display the number of disabled tests
      debug:
        var: test_results.disabled_tests
'''

RETURN = r'''
total_tests:
  description: The total number of tests in the JUnit report.
  type: int
disabled_tests:
  description: The number of disabled tests in the JUnit report.
  type: int
failed_tests:
  description: The number of failed tests in the JUnit report.
  type: int
error_tests:
  description: The number of tests with errors in the JUnit report.
  type: int
passed_tests:
  description: The number of passed tests in the JUnit report.
  type: int
results_summary:
  description: A short description summarizes the test results.
  type: str
'''


def parse_junit_test_results(xml_report):
    """
    Parse JUnit test results from an XML report.

    This function parses a JUnit XML report file and calculates the number of tests with different results.

    Args:
        xml_report (str): The path to the JUnit XML report file.

    Returns:
        dict: A dictionary containing the following keys:
            - total_tests (int): The total number of tests in the JUnit report.
            - disabled_tests (int): The number of disabled tests in the JUnit report.
            - failed_tests (int): The number of failed tests in the JUnit report.
            - error_tests (int): The number of tests with errors in the JUnit report.
            - passed_tests (int): The number of passed tests in the JUnit report.
            - error (str): An error message in case of module failure.
    """
    try:
        # validate the existence of the XML report file and parse it directly from the file
        with open(xml_report, 'r') as f:
            tree = ET.parse(f)
        root = tree.getroot()

        # extract relevant attributes
        total_tests = int(root.attrib["tests"])
        disabled_tests = int(root.attrib["disabled"])
        failed_tests = int(root.attrib["failures"])
        error_tests = int(root.attrib["errors"])

        # calculate the number of passed tests
        passed_tests = total_tests - disabled_tests - failed_tests - error_tests

        result = {
            "total_tests": total_tests,
            "disabled_tests": disabled_tests,
            "failed_tests": failed_tests,
            "error_tests": error_tests,
            "passed_tests": passed_tests
        }
        return result
    except FileNotFoundError:
        return {"error": "The {} report file does not exist.".format(xml_report)}
    except Exception as e:
        return {"error": str(e)}


def run_module():
    # define the AnsibleModule object with the available
    # arguments/parameters a user can pass to the module
    module = AnsibleModule(
        argument_spec=dict(
            xml_report=dict(type='str', required=True),
        )
    )

    # pars the parameters
    xml_report = module.params['xml_report']

    # seed the result dict in the object
    result = dict(
        changed=False,
        msg=''
    )

    junit_tests_result = parse_junit_test_results(xml_report)
    if 'error' in junit_tests_result:
        module.fail_json(
            msg="Failed to parse the JUnit results: {}".format(junit_tests_result['error']))
    else:
        result['total_tests'] = junit_tests_result['total_tests']
        result['disabled_tests'] = junit_tests_result['disabled_tests']
        result['failed_tests'] = junit_tests_result['failed_tests']
        result['error_tests'] = junit_tests_result['error_tests']
        result['passed_tests'] = junit_tests_result['passed_tests']
        result['results_summary'] = "{} total, {} passed, {} failed, {} error, {} disabled".format(junit_tests_result['total_tests'],
                                                                                                   junit_tests_result['passed_tests'],
                                                                                                   junit_tests_result['failed_tests'],
                                                                                                   junit_tests_result['error_tests'],
                                                                                                   junit_tests_result['disabled_tests'])
        result['msg'] = "The JUnit results were parsed successfully."

        if result['failed_tests'] > 0 or result['error_tests'] > 0:
            module.warn("Warning! {} tests failed, {} tests have errors".format(
                result['failed_tests'], result['error_tests']))

    module.exit_json(**result)


def main():
    run_module()


if __name__ == '__main__':
    main()
