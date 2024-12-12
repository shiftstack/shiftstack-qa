# Purpose
The goal of this role is to add DNS address entries to the `/etc/cifmw-dnsmasq.d/addresses.conf` file
in the cifmw-dnsmasq service running in the hypervisor:

```
address=/apps.ocp.openstack.lab/192.168.111.3
address=/<DOMAIN>/<IP>                         <-----
[...]
```

It will allow the RHOSO's management OCP pods to resolve shift-on-stack domains. The original file
is backed up so it can be restored once the DNS entries are not required anymore.

# Implementation
install+run dnsmasq and prepare the configuration to resolve the listed domains to the listed IPs.
There is another playbook within this function to revert the settings to the original state.

# Variables
This role requires two variables to be defined when importing it:

- tools_cifmw_dnsmasq_domains: includes a list of domains
- tools_cifmw_dnsmasq_ips: includes a list of ips

Both lists must be the same length, since the same index in each list represent together a DNS entry (domain/IP).

# Target host
The tasks in this role are expected to run in the hypervisor, so the target host needs to be delegated to the hypervisor, i.e.:

```
- ansible.builtin.import_role:
    name: tools_cifmw_dnsmasq
  vars:
    tools_cifmw_dnsmasq_domains:
      - "apps.{{ ocp_cluster_name }}.{{ ocp_base_domain }}"
    tools_cifmw_dnsmasq_ips:
      - "1.2.3.4"
  delegate_to: "{{ hypervisor }}"
  remote_user: root
```

It requires SSH passwordless login to the hypervisor (`rhos-dfg-osasinfra-qe.pub` in the hypervisor root user's `authorized_keys`,
injected by satellite).
https://issues.redhat.com/browse/SOSQE-2291
