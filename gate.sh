podman run -u root --pull always \
	-v .:/home/cloud-admin/shiftstack-qa:Z  \
	quay.io/shiftstack-qe/shiftstack-client \
	/bin/bash -c 'set -eu && cd shiftstack-qa && \
	  ansible-galaxy collection install -r requirements.yaml && \
	  ANSIBLE_VAULT_PASSWORD_FILE=/home/cloud-admin/.vault-pass pre-commit run --all-files'
#EOF
