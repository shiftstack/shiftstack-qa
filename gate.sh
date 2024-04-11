#!/bin/bash
echo 1. Re-create virtualenv
rm -rf .venv_precommit
python -m venv .venv_precommit
source .venv_precommit/bin/activate
pip install pre-commit setuptools
pre-commit install
pre-commit clean
echo
echo 3. Run pre-commit
ansible-galaxy install -r requirements.yaml
echo $VAULT > 'xx'
ANSIBLE_VAULT_PASSWORD_FILE='xx' pre-commit run
