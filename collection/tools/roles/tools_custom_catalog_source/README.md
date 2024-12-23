# Purpose

The goal is to create a catalog source for the GA version of OpenShift. This ensures that Red Hat and Certified Operators are available
in the pre-released versions.

# Implementation

1. **Retrieve the Latest OpenShift GA Version**:
   - Downloads the latest OpenShift release metadata from the official OpenShift mirror.
   - Extracts the version number using a regex pattern.
   - Sets the extracted version as a fact for later use.

2. **Create Custom Catalog Sources**:
   - Defines and applies custom `CatalogSource` resources for Red Hat Operators and Certified Operators.
   - These sources point to the appropriate operator index images, using the extracted OpenShift version.

3. **Wait for Catalog Sources to Become Available**:
   - Uses `oc wait` to ensure that the custom catalog sources are successfully deployed and available for use.

# Variables

This role requires the following variables to be defined:

- `ocp_release_url`: URL to fetch the OpenShift release metadata.
- `kubeconfig`: Path to the Kubernetes configuration file.
