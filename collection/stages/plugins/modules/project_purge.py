#!/usr/bin/python

from ansible_collections.openstack.cloud.plugins.module_utils.openstack import OpenStackModule
from openstack import exceptions as openstack_exceptions

DOCUMENTATION = '''
---
module: project_purge
short_description: Purge all resources in an OpenStack project
version_added: "1.0.0"
author: "Itay Matza"
description:
  - Purge all resources in a specified OpenStack project.
options:
  cloud:
    description:
      - Cloud configuration to use.
    required: true
    type: str
  project:
    description:
      - Name of the project to purge resources from.
    required: true
    type: str
  keep_project:
    description:
      - Whether to keep the project after purging resources.
    default: false
    type: bool
  remove_external_networks:
    description:
      - Whether to remove external networks as part of the network purge.
    default: false
    type: bool
'''

EXAMPLES = '''
# Purge all resources in a project and delete the project
- name: Purge OpenStack project
  project_purge:
    cloud: mycloud
    project: myproject

# Purge all resources but keep the project
- name: Purge OpenStack project resources
  project_purge:
    cloud: mycloud
    project: myproject
    keep_project: true

# Purge all resources and remove external networks
- name: Purge OpenStack project and remove external networks
  project_purge:
    cloud: mycloud
    project: myproject
    remove_external_networks: true
'''

RETURN = '''
changed:
  description: Whether any changes were made.
  type: bool
  returned: Always
messages:
  description: A list of logs and messages.
  type: list
  returned: Always
'''

RESOURCE_HANDLERS = {
    'floating_ip': {
        'list': lambda conn, filters: conn.network.ips(details=True, **filters),
        'delete': lambda conn, resource_id: conn.network.delete_ip(resource_id)
    },
    'router': {
        'list': lambda conn, filters: conn.network.routers(details=True, **filters),
        'delete': lambda conn, resource_id: conn.network.delete_router(resource_id)
    },
    'snapshot': {
        'list': lambda conn, filters: conn.block_storage.snapshots(details=True, **filters),
        'delete': lambda conn, resource_id: conn.block_storage.delete_snapshot(resource_id)
    },
    'volume': {
        'list': lambda conn, filters: conn.block_storage.volumes(details=True, **filters),
        'delete': lambda conn, resource_id: conn.block_storage.delete_volume(resource_id)
    },
    'server': {
        'list': lambda conn, filters: conn.compute.servers(details=True, **filters),
        'delete': lambda conn, resource_id: conn.compute.delete_server(resource_id)
    },
    'port': {
        'list': lambda conn, filters: conn.network.ports(details=True, **filters),
        'delete': lambda conn, resource_id: conn.network.delete_port(resource_id)
    },
    'subnet': {
        'list': lambda conn, filters: conn.network.subnets(details=True, **filters),
        'delete': lambda conn, resource_id: conn.network.delete_subnet(resource_id)
    },
    'network': {
        'list': lambda conn, filters: conn.network.networks(details=True, **filters),
        'delete': lambda conn, resource_id: conn.network.delete_network(resource_id)
    },
    'image': {
        'list': lambda conn, filters: conn.image.images(details=True, **filters),
        'delete': lambda conn, resource_id: conn.image.delete_image(resource_id)
    },
    'security_group': {
        'list': lambda conn, filters: conn.network.security_groups(details=True, **filters),
        'delete': lambda conn, resource_id: conn.network.delete_security_group(resource_id)
    },
    'stack': {
        'list': lambda conn, filters: conn.orchestration.stacks(details=True, **filters),
        'delete': lambda conn, resource_id: conn.orchestration.delete_stack(resource_id)
    },
    'swift_container': {
        'list': lambda conn, filters: conn.object_store.containers(details=True, **filters),
        'delete': lambda conn, resource_id: conn.object_store.delete_container(resource_id)
    },
}


class ProjectPurge(OpenStackModule):
    argument_spec = dict(
        project=dict(required=True),
        keep_project=dict(type='bool', default=False),
        remove_external_networks=dict(type='bool', default=False)
    )

    def run(self):
        """
        Main execution method called by Ansible.

        This method performs the purge operation on the specified OpenStack project,
        deleting all resources and optionally deleting the project itself.
        """
        project = self.params['project']
        keep_project = self.params['keep_project']
        remove_external_networks = self.params['remove_external_networks']
        self.results = dict(
            changed=False,
            messages=[]
        )

        try:
            project_obj = self.conn.identity.find_project(project,
                                                          ignore_missing=False)
            project_id = project_obj.id

            for resource, handler in RESOURCE_HANDLERS.items():
                resource_info = self.gather_resource_info(resource,
                                                          project_id,
                                                          remove_external_networks)
                if resource_info:
                    for res in resource_info:
                        self.log(f"Deleting {resource} with ID: {res.id}")
                        self.delete_resource(resource, res)

            if not keep_project:
                try:
                    self.conn.identity.delete_project(project_id)
                    self.log(f"Project {project} deleted successfully")
                except openstack_exceptions.ConflictException as e:
                    self.fail(msg=f"Failed to delete project {project}: {str(e)},",
                              **self.results)

            self.results['changed'] = True
            self.exit(
                msg=f"Project {project} purged successfully", **self.results)

        except Exception as e:
            self.fail(
                msg=f"Failed to purge project {project}: {str(e)}", **self.results)

    def gather_resource_info(self, resource, project_id, include_external_networks):
        """
        Gather information about resources to be purged.

        Args:
            resource (str): Type of resource to gather information for.
            project_id (str): ID of the OpenStack project.
            include_external_networks (bool): Whether to include external networks.

        Returns:
            list: List of resources to be purged.

        Raises:
            Exception: If the specified resource type is not supported.
        """
        handler = RESOURCE_HANDLERS.get(resource)
        if handler:
            list_method = handler['list']
            filters = {'project_id': project_id}
            if resource == 'network' and not include_external_networks:
                filters['router:external'] = False
            return list(list_method(self.conn, filters=filters))
        else:
            raise Exception(f"Unsupported resource type: {resource}")

    def delete_resource(self, resource, res):
        """
        Delete a specific resource.

        Args:
            resource (str): Type of resource to delete.
            res (object): Resource object to delete.

        Raises:
            Exception: If the specified resource type is not supported.
        """
        handler = RESOURCE_HANDLERS.get(resource)
        if handler:
            delete_method = handler['delete']
            if resource == 'port':
                if res.device_owner == 'network:router_interface':
                    self.conn.network.remove_interface_from_router(
                        res.device_id, port_id=res.id)
                    self.log(
                        f"Detached port {res.id} from router {res.device_id}")
                elif res.device_owner == 'network:router_gateway':
                    self.conn.network.update_router(
                        res.device_id, external_gateway_info=None)
                elif res.device_owner == 'network:floatingip':
                    floating_ip = self.conn.network.find_ip(
                        res.fixed_ips[0]['ip_address'])
                    self.conn.network.update_ip(floating_ip.id, port_id=None)
            elif resource == 'router':
                interfaces = self.conn.network.ports(
                    filters={'device_id': res.id})
                for iface in interfaces:
                    self.log(
                        f"Detaching interface {iface.id} from router {res.id}")
                    try:
                        self.conn.network.remove_interface_from_router(
                            res.id, port_id=iface.id)
                        self.log(
                            f"Detached interface {iface.id} from router {res.id}")
                    except Exception as e:
                        self.log(
                            f"Failed to detach interface {iface.id} from router {res.id}: {str(e)}")
            delete_method(self.conn, res.id)
            self.log(f"{resource} with ID: {res.id} deleted successfully")
        else:
            raise Exception(f"Unsupported resource type: {resource}")

    def log(self, msg):
        """
        Prints log message to system log and append to the results "messages".

        Arguments:
            msg (str): Log message.
        """
        self.results['messages'].append(msg)
        self.ansible.log(msg)


if __name__ == '__main__':
    module = ProjectPurge()
    module()
