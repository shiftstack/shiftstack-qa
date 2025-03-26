# Purpose

The MCE team is uploading pre-released versions of the MultiClusterEngine (MCE)  operator into quay.io.

The productized (downstream) MultiClusterEngine (MCE) builds are published to quay.io/acm-d repo currently. This role configures the openshift to be able to download the latest pre-released versions for the MCE Operator.

The procedure is completely inspired on https://steps.ci.openshift.org/reference/hypershift-mce-install

# Implementation
In order to configure the cluster to access to these versions, it's required to:

- Install a custom-mce sourceCatalog pointing to quay.io:443/acm-d.
- Add the quay.io auth with the key that is configured as a robot puller in the quay.io/acm-d
    - __Note__: In order to avoid overwrite of quay.io already present, we are using quay.io:443 instead of quay.io.
    - https://quay.io/organization/acm-d/teams/pullers

- Add to the cluster an ImageContentSourcePolicy object, so every pull related to multicluster-engine is mirrored to quay.io:443.

# Variables

- tools_install_custom_mce_catalog_channel(default: 'default'): Dictionary that pairs the expected MCE version with to the Openshift release.
    - __Warning!__ There is no default value, so the automation will fail if the key is not present.
- custom_catalog_name(default: 'custom-mce-catalog'): String that defines the name of the Catalog Source that will be deployed to the cluster by this role. Make sure to use this exact name in any subsequent tasks that need to access this catalog.