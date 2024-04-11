#!/bin/bash
echo 1. Re-create virtualenv
rm -rf /tmp/venv_precommit
python -m venv /tmp/venv_precommit
source /tmp/venv_precommit/bin/activate
pip install --upgrade pip
pip install --upgrade setuptools
pip install pre-commit
echo DEBUG
pip freeze | grep setuptools
pre-commit install
pre-commit clean
echo
echo 3. Run pre-commit
ansible-galaxy install -r requirements.yaml
echo $VAULT > 'xx'
ANSIBLE_VAULT_PASSWORD_FILE='xx' pre-commit run
