#!/bin/bash
echo 1. Re-create virtualenv
rm -rf ~/venv_precommit
python -m venv ~/venv_precommit
. ~/venv_precommit/bin/activate
pip install pre-commit ansible-core
pre-commit install
pre-commit clean
echo
echo 2. Clone patch
git clone https://review.gerrithub.io/shiftstack/shiftstack-qa ~/venv_precommit/shiftstack-qa/
cd ~/venv_precommit/shiftstack-qa/
git fetch https://review.gerrithub.io/shiftstack/shiftstack-qa $GERRIT_REFSPEC
echo
echo 3. Run pre-commit
ansible-galaxy install -r requirements.yaml
echo $VAULT > 'xx'
ANSIBLE_VAULT_PASSWORD_FILE='xx' pre-commit run
