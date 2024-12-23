# Purpose

The goal is to install Red Hat OpenShift AI operator with the dependencies (ServiceMesh, Serverless).

# Implementation

The implementation is based on a series of tasks to install the necessary operators for OpenShift AI. The deployment consists of the following steps:

1. **Install Custom Catalog Source (Optional)**:
   - If `use_custom_catalog_source` is enabled, this task installs a custom catalog source using the `shiftstack.tools.tools_custom_catalog_source` role.

2. **Install ServiceMesh Operator**:
   - Installs the ServiceMesh Operator, which provides the capabilities for deploying and managing Istio-based service meshes.

3. **Install Serverless Operator**:
   - Installs the Serverless Operator, which facilitates the deployment of Knative-based serverless workloads on OpenShift.

4. **Install RHOAI Operator**:
   - Installs the OpenShift AI operator and create Data Science cluster

# Variables

This role requires the following variables to be defined:

- `use_custom_catalog_source`: Boolean to determine whether to install a custom catalog source.
- `kubeconfig`: Path to the Kubernetes configuration file.
