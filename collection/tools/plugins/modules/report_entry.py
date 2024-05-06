#!/usr/bin/python3

# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
from logging import exception
import time
from ansible.module_utils.basic import AnsibleModule
import gspread
from gspread_formatting import *
from oauth2client.service_account import ServiceAccountCredentials
__metaclass__ = type

MAX_RETRY_ATTEMPTS = 5  # Maximum number of retry attempts
SLEEP_DELAY = 1  # Delay in seconds

DOCUMENTATION = r'''
---
module: report_entry

short_description: Report job results on given spreadsheet.

version_added: "1.0.0"

description:
  - This Ansible module parses a CSV entry and write an entry on a given google spreadsheet.

author: Ramon Lobillo

'''

EXAMPLES = r'''
TBD
'''

RETURN = r'''
TBD
'''

def run_module():
    # define the AnsibleModule object with the available
    # arguments/parameters a user can pass to the module
    module = AnsibleModule(
        argument_spec=dict(
            credentials=dict(type='dict', required=True),
            job_name=dict(type='str', required=True),
            header=dict(type='str', required=True),
            input=dict(type='str', required=True),
            output_spreadsheet=dict(type='str', required=True),
        )
    )

    # parse the parameters
    credentials = module.params['credentials']
    output_spreadsheet = module.params['output_spreadsheet']
    job_name = module.params['job_name']
    header = module.params['header']
    input = module.params['input']
    write_scope = ['https://www.googleapis.com/auth/drive']
    write_creds = ServiceAccountCredentials.from_json_keyfile_dict(credentials, write_scope)
    write_client = gspread.authorize(write_creds)
    write_book = retry_gspread_operation(write_client.open, output_spreadsheet)

    # logic
    try:
        write_sheet = get_spreadsheet(write_book, header, job_name)
        write_sheet.insert_rows([input.split(',')], row=2, value_input_option='USER_ENTERED')
        result = dict(
            changed=True,
            msg='Data successfully reported.'
        )

    except exception as e:
        module.fail_json(
            msg="Failed: %e". e)

    module.exit_json(**result)

def retry_gspread_operation(func, *args, **kwargs):
    """
    Retries the execution of a gspread operation in case of exceptions.

    Args:
        func: The function to be retried.
        *args: Positional arguments to be passed to the function.
        **kwargs: Keyword arguments to be passed to the function.

    Returns:
        The return value of the function.

    Raises:
        gspread.exceptions.GSpreadException: If the maximum number of retry attempts is reached.
    """
    retry_count = 0
    backoff_delay = SLEEP_DELAY

    while retry_count < MAX_RETRY_ATTEMPTS:
        try:
            return func(*args, **kwargs)  # Execute the provided function with arguments

        except gspread.exceptions.GSpreadException as exception:
            retry_count += 1
            print(f"Encountered GSpreadException: {exception}")

            if retry_count < MAX_RETRY_ATTEMPTS:
                print(f"Retrying in {backoff_delay} seconds... (Attempt {retry_count}/{MAX_RETRY_ATTEMPTS})")
                time.sleep(backoff_delay)
                backoff_delay *= 2  # Exponential backoff: double the delay for each retry
            else:
                print("Maximum retry attempts reached.")
                raise exception

def get_spreadsheet(book, headers, title):
    '''''
    Look for a sheet with the given title on the given book
    and creates it (adding headers) if it does not exist.
    '''''

    worksheets = retry_gspread_operation(book.worksheets)
    if title not in [i.title for i in worksheets]:
        sheet = retry_gspread_operation(book.add_worksheet, title, 2, 1)
        sheet.append_row(headers)
        sheet.format("A1:Z1", {"textFormat": {"bold": True}})
    else:
        sheet = retry_gspread_operation(book.worksheet, title)
    return sheet


def main():
    run_module()


if __name__ == '__main__':
    main()
