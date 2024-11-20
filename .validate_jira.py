#!/usr/bin/env python3
import sys
import re
import logging

# Configure logging to send all levels to stderr and ensure visibility on the terminal
logging.basicConfig(
    level=logging.INFO,
    format="%(levelname)s: %(message)s",
    handlers=[
        logging.StreamHandler(sys.stderr),
        logging.StreamHandler(open("/dev/tty", "w"))  # Ensure messages appear on terminal
    ]
)

# Jira configurations
JIRA_BASE_URL = "https://issues.redhat.com/browse/"
JIRA_PATTERN = r"[A-Z]+-[0-9]+"  # Pattern to match Jira IDs
JIRA_URL_PATTERN = rf"{JIRA_BASE_URL}{JIRA_PATTERN}"  # Full Jira URL pattern


def read_commit_message(file_path):
    """Reads the commit message file and returns the lines as a list."""
    try:
        with open(file_path, "r") as file:
            return file.readlines()
    except FileNotFoundError:
        logging.error(f"Commit message file '{file_path}' not found.")
        sys.exit(1)


def validate_commit_message_lines(lines):
    """
    Validates the commit message lines for the following:
    - At least 3 lines are present.
    - Second line is blank.
    - Third line contains a valid Jira ID or full Jira URL.
    """
    logging.info("Starting commit message validation")
    if len(lines) < 3:
        logging.warning("The commit message should contain the main Jira task in the 3rd line.")

    # Validate the first line length
    first_line = lines[0].strip()
    if len(first_line) > 72:
        logging.warning("The first line of the commit message exceeds 72 characters. Consider shortening it.")

    # Validate the second line is blank
    if lines[1].strip() != "":
        logging.warning("The second line of the commit message is not blank. Consider adding a blank line for readability.")

    # Validate the third line contains a valid Jira ID or URL
    third_line = lines[2].strip()
    if re.fullmatch(JIRA_URL_PATTERN, third_line):
        logging.debug("Commit message validation passed. Full Jira URL already present.")
    elif re.match(JIRA_PATTERN, third_line):
        # Replace Jira ID with the full URL
        lines[2] = f"{JIRA_BASE_URL}{third_line}\n"
        with open(commit_msg_file, "w") as file:
            file.writelines(lines)
        logging.info("Commit message validation passed. Jira ID replaced with full URL.")
    else:
        logging.warning(f"Line 3 should contain a Jira task ID in the format PROJECT-123 or a valid URL.")


if __name__ == "__main__":
    # Ensure the script is called with the correct arguments
    if len(sys.argv) != 2:
        logging.error("Usage: validate_jira.py <commit_msg_file>")
        sys.exit(1)

    commit_msg_file = sys.argv[1]
    commit_lines = read_commit_message(commit_msg_file)
    validate_commit_message_lines(commit_lines)
