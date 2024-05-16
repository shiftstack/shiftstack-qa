podman run --pull always \
	-v .:/home/cloud-admin/shiftstack-qa:Z  \
	quay.io/shiftstack-qe/shiftstack-client \
	/bin/bash -c 'cd shiftstack-qa && \
	  ansible-galaxy install -r requirements.yaml && \
	  git config --global init.templateDir ~/.git-template && pre-commit init-templatedir ~/.git-template && pre-commit install && \
	  pre-commit run && \
	  cd && \
	  ansible-navigator run shiftstack-qa/playbooks/ocp_testing.yaml --extra-vars @shiftstack-qa/jobs_definitions/cifmw-gate.yaml -vvv'
#EOF
