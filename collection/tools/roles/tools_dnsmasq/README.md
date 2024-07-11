# Purpose

The goal of this role is to setup a DNSMASQ service that will resolve all the potential new domains pointing to the shiftstack cluster:

```
resolv-file=/etc/resolv.orig
address=/<DOMAIN>/<IP>
[...]
```

This is needed for running conformance testsuite, there are some cases that creates a route in openshift and they should be
appropiatedly resolved from the place where the tests are run.

# Implementation

This role is installing dnsmasq and preparing its configuration based on the existing /etc/hosts.
It is also backing up the existing /etc/resolv.conf configuration and creating another one that points to the localhost dnsmasq.

There is another specific playbook inside this role to revert the configuration back to the original status.

# Variables
This role requires that two variables are defined:

- tools_dnsmasq.domains: including a list of domains.
- tools_dnsmasq.ips: including a list of ips

Both lists should have the same length.

