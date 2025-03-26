# Purpose

Install openshift operator on a given openshift cluster (defined by kubeconfig)

# Implementation

- Create the namespace
- Create the operatorGroup
- Create the subscription
- Wait until the operator pods are deployed
- Create a resource from the API provided by the operator (if install_openshift_operator_provided_api is defined)
- Wait until the resource is deployed

# Variables

- install_openshift_operator_namespace(default: 'default'): Namespace where the operator will be installed.
- install_openshift_operator_catalogsource (default: 'redhat-operators'): CatalogSource where the operator is.
- install_openshift_operator_name: The name of the operator.
- install_openshift_operator_package: The operator package for detecting the defaultChannel.
- install_openshift_operator_provided_api: The name of the resource added by the operator. If defined, the role will create one with default values.
