#!/bin/bash

HOME_DIR=/home/stack
GERRIT_CHANGE="refs/changes/25/1212225/2"
if [[ -n "$GERRIT_CHANGE" ]]; then 
  CHECKOUT_PATCH="&& git fetch https://gerrithub.io/shiftstack/shiftstack-qa $GERRIT_CHANGE && git checkout FETCH_HEAD"
else
  CHECKOUT_PATCH=""
fi

if [[ ! -d $HOME_DIR/artifacts ]]; then sudo rm -rf $HOME_DIR/artifacts; fi
mkdir -p -m 777 $HOME_DIR/artifacts/ansible_logs

COMMAND="git clone https://gerrithub.io/shiftstack/shiftstack-qa && cd /home/cloud-admin/shiftstack-qa \
     $CHECKOUT_PATCH && ansible-galaxy collection install -r requirements.yaml -f  && \
     ansible-navigator run playbooks/hypershift_testing.yaml -e job_definition=gate.yaml"
echo $COMMAND
podman run --pull always --security-opt seccomp=unconfined \
  -v $HOME_DIR/artifacts:/home/cloud-admin/artifacts:z \
  -v $HOME_DIR/clouds.yaml:/home/cloud-admin/.original-config/openstack/clouds.yaml:ro \
  -v /etc/pki/ca-trust/source/anchors/undercloud-cacert.pem:/etc/pki/ca-trust/source/anchors/undercloud-cacert.pem:ro \
  quay.io/shiftstack-qe/shiftstack-client bash -c "$COMMAND"

