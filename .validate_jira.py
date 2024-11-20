#!/usr/bin/env python3
import sys
import re

def validate_commit_message(commit_msg_file):
    """
    Validate that the commit message follows the convention:
    - At least 3 lines.
    - Second line is blank.
    - Third line contains a valid Jira ID in the format PROJECT-123 or a full URL.
    Replace the Jira ID with a full URL if it's not already a URL.
    """
    jira_pattern = r"[A-Z]+-[0-9]+"  # Pattern to match Jira IDs
    jira_base_url = "https://issues.redhat.com/browse/"  # Replace with your Jira base URL

    try:
        with open(commit_msg_file, "r") as file:
            commit_lines = file.readlines()
    except FileNotFoundError:
        print(f"Error: Commit message file '{commit_msg_file}' not found.")
        sys.exit(1)

    # Check for at least 3 lines
    if len(commit_lines) < 3:
        print("Error: Commit message must have at least 3 lines.")
        print("Line 3 must contain the primary Jira task ID in the format PROJECT-123 or a full Jira URL.")
        sys.exit(1)

    # Ensure the first line is concise (72 characters max)
    first_line = commit_lines[0].strip()
    if len(first_line) > 72:
        print("Error: The first line of the commit message must be less than 72 characters.")
        sys.exit(1)

    # Validate second line is blank
    if commit_lines[1].strip() != "":
        print("Error: The second line of the commit message must be blank for readability.")
        sys.exit(1)

    # Validate and potentially replace the third line
    third_line = commit_lines[2].strip()
    if third_line.startswith(jira_base_url):
        # The third line is already a full Jira URL, no further action needed
        print("Commit message validation passed. Full Jira URL already present.")
    elif re.match(jira_pattern, third_line):
        # The third line contains a Jira ID, replace it with the full URL
        commit_lines[2] = f"{jira_base_url}{third_line}\n"
        with open(commit_msg_file, "w") as file:
            file.writelines(commit_lines)
        print("Commit message validation passed. Jira ID replaced with full URL.")
    else:
        # The third line does not match either a Jira ID or a valid URL
        print("Error: The third line must contain a Jira task ID in the format PROJECT-123 or a valid Jira URL.")
        sys.exit(1)

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: validate_jira.py <commit_msg_file>")
        sys.exit(1)

    validate_commit_message(sys.argv[1])
