# Purpose

The goal of this role is to setup a DNSMASQ process that will resolve all the potential new domains pointing to the defined IPs:

```
resolv-file=/etc/resolv.orig
address=/<DOMAIN>/<IP>
[...]
```

This is needed for running conformance testsuite, there are some cases that creates a route in openshift and they should be
appropiatedly resolved from the place where the tests are run.

# Implementation

This role is installing+running dnsmasq and preparing its configuration to resolve listed domains to listed IPs.
There is another playbook inside this role to revert the configuration back to the original status.

# Variables
This role requires that two variables are defined:

- tools_dnsmasq_domains: including a list of domains.
- tools_dnsmasq_ips: including a list of ips

Both lists should have the same length as they are zipped lists mapped together (1st domain resolves to 1st IP and so on).

