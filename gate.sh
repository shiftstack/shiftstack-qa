podman run -u root --pull always \
	-v .:/home/cloud-admin/shiftstack-qa:O  \
	quay.io/shiftstack-qe/shiftstack-client \
	/bin/bash -c 'cd shiftstack-qa && \
	  ansible-galaxy install -r requirements.yaml && \
	  ANSIBLE_VAULT_PASSWORD_FILE=/home/cloud-admin/.vault-pass pre-commit run'
#EOF
