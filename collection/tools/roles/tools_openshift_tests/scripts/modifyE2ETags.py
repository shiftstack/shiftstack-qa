#!/usr/bin/python3

from lxml import etree
import sys
import time

# Mapping of testsuite names whose tests originate from openshift-tests-private
# and need classname remapped to match the Polarion naming convention used by
# the main openstack test suites (sig-installer.Suite_openshift_openstack.*).
PRIVATE_TEST_SUITES = {
    'egressip_tests': 'sig-installer.Suite_openshift_openstack.egressip',
}


def format_test_case_name(s):
    return s.replace(':', '_').replace('/', '_').replace(' ', '_').replace('.', '_').replace('[', '.').replace(']', '.').rstrip('.').replace('..','.').replace('_.','.').replace('._','.')[1::]


def remap_private_test_name(tc_name, testsuite_name):
    """Remap openshift-tests-private names to Polarion-compatible format.

    Tests from openshift-tests-private use [sig-networking] SDN_OVN_EgressIP_*
    naming which JUMP cannot match. Remap to the sig-installer.Suite_openshift_openstack
    pattern that has registered Polarion test case entries.
    """
    prefix = PRIVATE_TEST_SUITES.get(testsuite_name)
    if not prefix:
        return None
    short_name = format_test_case_name(tc_name)
    # Strip the sig-networking (or similar) classname prefix from Ginkgo output
    if '.' in short_name:
        _, short_name = short_name.split('.', 1)
    return f"{prefix}.{short_name}"


# Self-test mode: verify transform logic without processing XML files.
if len(sys.argv) == 2 and sys.argv[1] == '--self-test':
    egressip_input = (
        '[sig-networking] SDN OVN EgressIP Author:huirwang-ConnectedOnly-Medium-47272-'
        '.FdpOvnOvs.Pods will not be affected by the egressIP set on other netnamespace .Serial'
    )
    result = remap_private_test_name(egressip_input, 'egressip_tests')
    assert result.startswith('sig-installer.Suite_openshift_openstack.egressip.SDN_OVN_EgressIP_'), \
        f"Unexpected remap result: {result}"

    assert remap_private_test_name(egressip_input, 'unknown_suite') is None, \
        "Unknown suite should return None"

    otp_input = '[OTP][sig-installer] Suite openshift openstack lb Serial test'
    otp_result = format_test_case_name(otp_input)
    assert otp_result.startswith('OTP.sig-installer'), \
        f"OTP prefix not preserved by format_test_case_name: {otp_result}"

    print("All self-tests passed.")
    sys.exit(0)

# This script modify a given xml report so it can be uploaded to ReportPortal and Polarion.
# @arg1: input xml file.
# @arg2: output xml file.
# @arg3: Tests to include
# @arg4: testSuite name.

if len(sys.argv) != 5:
    sys.exit('wrong number of arguments')

parser = etree.XMLParser(encoding='utf-8', recover=True, huge_tree=True)
root = etree.parse(str(sys.argv[1]), parser=parser).getroot()
outputfile = str(sys.argv[2])
tests = str(sys.argv[3])
testsuite_name = str(sys.argv[4])

# To meet droute requirements:
if 'duration' in root.attrib:
  del root.attrib['duration']

for ts in root:
  if 'tests' in ts.keys() and \
    (ts.get('tests') == '0' or ts.get('tests') == ts.get('skipped')):
    print('TestSuite removed because it includes the attrib', \
        'tests set to 0 or to an equal value than the skipped attribute: ', ts.attrib)
    root.remove(ts)
  else:
    ts.set('name', testsuite_name)
    print('TestSuite name changed to', tests)

    for tc in ts:
        if tc.tag == 'properties':
           ts.remove(tc)
           print('Removing properties from the testsuite', ts.get('name'))
        else:
            tc_name = tc.get('name')
            if tc_name:
                if not tests.lower() in tc_name.lower():
                    print('TestCase removed from input XML:', tc_name)
                    ts.remove(tc)
                else:
                    remapped = remap_private_test_name(tc_name, testsuite_name)
                    if remapped:
                        new_tc_name = remapped
                    else:
                        new_tc_name = format_test_case_name(tc_name)
                        if new_tc_name.startswith('OTP.'):
                            new_tc_name = new_tc_name[4:]

                    if '.' in new_tc_name:
                        tc_classname, tc_name_rest = new_tc_name.split('.', 1)
                        tc.set('classname', tc_classname)
                        tc.set('name', tc_name_rest)
                    else:
                        tc.set('name', new_tc_name)
                    print('TestCase added to output XML:', new_tc_name)
    ts.set('tests', str(len(ts.getchildren())))

et = etree.ElementTree(root)
et.write(outputfile)
