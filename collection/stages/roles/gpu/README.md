# Purpose

The goal is to deploy the NVIDIA GPU Operator and the Node Feature Discovery (NFD) Operator on OpenShift.

# Implementation

The implementation is based on the official NVIDIA documentation: [NVIDIA GPU Operator for OpenShift 23.9.2](https://docs.nvidia.com/datacenter/cloud-native/openshift/23.9.2/index.html).

The deployment consists of multiple steps:

1. **Install Custom Catalog Source (Optional)**:
   - If `use_custom_catalog_source` is enabled, installs a custom catalog source using the `shiftstack.tools.tools_custom_catalog_source` role.

2. **Deploy the NFD Operator**:
   - Installs the Node Feature Discovery Operator, which detects and labels nodes with hardware features, including GPUs.

3. **Deploy the NVIDIA GPU Operator**:
   - Installs the NVIDIA GPU Operator.

4. **Verify Worker Nodes**:
   - Retrieves the total number of worker nodes in the cluster and ensures at least one worker node is available.

5. **Scale Up Non-GPU Worker Node (if needed)**:
   - If there are fewer than two worker nodes and GPU worker nodes exist, a non-GPU worker node is scaled up.

# Variables

This role requires the following variables to be defined:

- `use_custom_catalog_source`: Boolean to determine whether to install a custom catalog source.
- `kubeconfig`: Path to the Kubernetes configuration file.
