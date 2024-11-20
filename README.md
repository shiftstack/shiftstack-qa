# shiftstack-qa
Ansible playbooks and roles for QA automation for OSP18 and up.

[![pre-commit](https://img.shields.io/badge/pre--commit-enabled-brightgreen?logo=pre-commit)](https://github.com/pre-commit/pre-commit)

## Requirements
1. This code is intended to run on top of the image https://quay.io/repository/shiftstack-qe/shiftstack-client
2. The container must have access to the Openstack API and the external Openstack network.
3. The container should have internet access.
4. The container should have the vault-password-file in the expected place.

## Install
```
oc rsh shiftstackclient -n openstack \
  git clone https://github.com/shiftstack/shiftstack-qa.git
oc rsh shiftstackclient -n openstack \
  cd shiftstack-qa && ansible-galaxy collection install -r requirements.yaml -f
```
where:
- [requirements](./requirements.yaml) includes the dependencies and the local collection.
- [shiftstack.stages](./collection/stages): The local collection including the automation.

## Run
You can list the tasks on a playbook:
```
oc rsh shiftstackclient -n openstack \
  ansible-navigator run shiftstack-qa/playbooks/{playbook_name}.yaml --list-tasks
```

For running:
```
oc rsh shiftstackclient -n openstack \
  ansible-navigator run shiftstack-qa/playbooks/{playbook_name}.yaml --extra-vars @shiftstack-qa/jobs_definitions/{job_definition_name}.yaml
```

where:
- [playbooks](./playbooks) includes one playbook per scenario to be tested (formerly known as a job template).
- [jobs_definitions](./jobs_definitions) includes one job configuration to be tested using the playbook (formerly known as job pipeline).

## Troubleshooting
Thanks to ``ansible-navigator``, the run generates JSON file with format:
```
/home/shifstack/artifacts/{playbook_name}-artifact-{time_stamp}.json
```
You can easily replay the run & troubleshoot in interactive mode with:
```
oc rsh shiftstackclient -n openstack \
  ansible-navigator replay /home/cloud-admin/artifacts/{playbook_name}-artifact-{time_stamp}.json -m interactive
```

## Pre-Commit Hooks
This project uses `pre-commit` to enforce coding standards and commit message validation.

### About Hook Types
- **Pre-commit stage hooks**: Validate staged files before committing (e.g., linting YAML files with `ansible-lint`).
- **Commit-msg hooks**: Validate the commit message after it's written but before the commit is finalized.

### Why Use Hooks?
Hooks ensure:
- Commit messages follow Git best practices (e.g., concise first line, blank second line).
- Traceability by enforcing Jira task links in commit messages.
- Consistency and readability across commits.

### Enable Hooks
To enable hooks, run:
```bash
pip install pre-commit
git config --global init.templateDir ~/.git-template
pre-commit init-templatedir ~/.git-template
pre-commit install
pre-commit install --hook-type commit-msg
```
