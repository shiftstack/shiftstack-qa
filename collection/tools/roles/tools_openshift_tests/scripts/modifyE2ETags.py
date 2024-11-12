#!/usr/bin/python3

from lxml import etree
import sys
import time

def format_test_case_name(s):
    return s.replace(':', '_').replace('/', '_').replace(' ', '_').replace('.', '_').replace('[', '.').replace(']', '.').rstrip('.').replace('..','.').replace('_.','.').replace('._','.')[1::]

# This script modify a given xml report so it can be uploaded to ReportPortal and Polarion.
# third argument. Currently it's used for NetworkPolicy and Conformance tests
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

test_time = str(int(time.time())).encode("utf-8")

# Remove the attribute 'id' from testsuites
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
    ts.set('timestamp', test_time)
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
                    new_tc_name = format_test_case_name(tc_name)
                    tc.set('name', new_tc_name)
                    print('TestCase added to output XML:', new_tc_name)
    ts.set('tests', str(len(ts.getchildren())))

et = etree.ElementTree(root)
et.write(outputfile)
