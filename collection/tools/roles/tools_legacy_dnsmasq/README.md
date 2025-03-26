# Purpose
The goal of this role is to populate a dnsmasq on legacy setups (RHOSP17.1).
By passing a list of domains and IP, it will create a separated dnsmasq.conf
and retrigger the service on the target node.

```
address=/apps.ocp.openstack.lab/192.168.111.3
address=/<DOMAIN>/<IP>                         <-----
[...]
```

# Implementation
install+run dnsmasq and prepare the configuration to resolve the listed
domains to the listed IPs.
There is another playbook within this function to revert the settings to
the original state.

# Variables
This role requires two variables to be defined when importing it:

- tools_legacy_dnsmasq_domains (list): includes a list of domains
- tools_legacy_dnsmasq_ips (list): includes a list of ips
- tools_legacy_dnsmasq_custom_conf (string): dnsmasq.conf path

Both lists must be the same length, since the same index in each list
represent together a DNS entry (domain/IP).

# Outcome

The role will fill a variable called `tools_legacy_dnsmasq_host_ip`
that will contain the IP from where the dnsmasq is listening on port 53.

# Target host
The tasks in this role are expected to run in the hypervisor, so the
target host needs to be delegated to the hypervisor.

It requires SSH passwordless login to the hypervisor
(`rhos-dfg-osasinfra-qe.pub` in the hypervisor root user's `authorized_keys`,
injected by satellite).
https://issues.redhat.com/browse/SOSQE-2291
