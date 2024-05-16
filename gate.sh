podman run --pull always \
	-v .:/home/cloud-admin/shiftstack-qa:Z  \
	quay.io/shiftstack-qe/shiftstack-client \
	/bin/bash -c 'cd shiftstack-qa && \
	  ansible-galaxy install -r requirements.yaml && \
	  export ANSIBLE_VAULT_PASSWORD_FILE=/home/cloud-admin/.vault-pass && \
	  pre-commit run && \
	  cd && \
	  ansible-navigator run shiftstack-qa/playbooks/ocp_testing.yaml --extra-vars @shiftstack-qa/jobs_definitions/cifmw-gate.yaml -vvv'
#EOF
