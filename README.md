# shiftstack-qe
Ansible playbooks and roles for QA automation for OSP18 and up.

## Requirements
1. This code is intended to run on top of the image https://quay.io/repository/shiftstack-qe/shiftstack-client
2. The container must have access to the Openstack API and the external Openstack network.
3. The container should have internet access.

## Install
```
oc rsh shiftstackclient -n openstack \
  git clone https://github.com/shiftstack/shiftstack-qe.git
oc rsh shiftstackclient -n openstack \
  cd shiftstack-qe && ansible-galaxy collection install -r requirements.yaml -f
```
where:
- [requirements](./requirements.yaml) includes the dependencies and the local collection.
- [shiftstack.stages](./collection/stages): The local collection including the automation.

## Run
```
oc rsh shiftstackclient -n openstack \
  ansible-navigator shiftstack-qe/playbooks/{playbook_name}.yaml
```
where:
- [playbooks](./playbooks) includes 1 playbook per scenario to be tested (formerly known as Job).

## Troubleshooting
Thanks to ``ansible-navigator``, the run generates JSON file with format:
```
/home/shifstack/artifacts/{playbook_name}-artifact-{time_stamp}.json
```
You can easily replay the run & troubleshoot in interactive mode with:
```
oc rsh shiftstackclient -n openstack \
  ansible-navigator replay /home/shifstack/artifacts/{playbook_name}-artifact-{time_stamp}.json -m interactive
```
