# Purpose

The goal is to configure a DNSMASQ process that will resolve all potential new domains pointing to the defined IPs:

```
resolv-file=/etc/resolv.orig
address=/<DOMAIN>/<IP>
[...]
```

This is necessary to run the conformance test suite, there are some cases that create a route in openshift and it needs to be
resolved from the place where the tests are carried out.

# Implementation

install+run dnsmasq and prepare the configuration to resolve the listed domains to the listed IPs.
There is another playbook within this function to revert the settings to the original state.

# Variables
This role requires two variables to be defined:

- tools_dnsmasq_domains: includes a list of domains.
- tools_dnsmasq_ips: includes a list of ips

Both lists must be the same length, since they are compressed lists mapped together (first domain resolves to first IP, etc.).