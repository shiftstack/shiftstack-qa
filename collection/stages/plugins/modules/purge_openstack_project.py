#!/usr/bin/python

from ansible_collections.openstack.cloud.plugins.module_utils.openstack import OpenStackModule
from openstack import exceptions as openstack_exceptions
from neutronclient.exceptions import NetworkNotFound

DOCUMENTATION = '''
---
module: project_purge
short_description: Purge all resources in an OpenStack project
version_added: "1.0.0"
author: "Your Name"
description:
  - This module purges all resources in a specified OpenStack project.
options:
  cloud:
    description:
      - Cloud configuration to use.
    required: true
    type: str
  project_name:
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
    project_name: myproject

# Purge all resources but keep the project
- name: Purge OpenStack project resources
  project_purge:
    cloud: mycloud
    project_name: myproject
    keep_project: true

# Purge all resources and remove external networks
- name: Purge OpenStack project and remove external networks
  project_purge:
    cloud: mycloud
    project_name: myproject
    remove_external_networks: true
'''

RETURN = '''
changed:
  description: Whether any changes were made.
  type: bool
  returned: always
msg:
  description: The outcome of the module.
  type: str
  returned: always
'''

RESOURCE_HANDLERS = {
    'floating_ip': {'list': 'network.ips', 'delete': 'network.delete_ip'},
    'router': {'list': 'network.routers', 'delete': 'network.delete_router'},
    'snapshot': {'list': 'block_storage.snapshots', 'delete': 'block_storage.delete_snapshot'},
    'volume': {'list': 'block_storage.volumes', 'delete': 'block_storage.delete_volume'},
    'server': {'list': 'compute.servers', 'delete': 'compute.delete_server'},
    'port': {'list': 'network.ports', 'delete': 'network.delete_port'},
    'subnet': {'list': 'network.subnets', 'delete': 'network.delete_subnet'},
    'network': {'list': 'network.networks', 'delete': 'network.delete_network'},
    'image': {'list': 'image.images', 'delete': 'image.delete_image'},
    'security_group': {'list': 'network.security_groups', 'delete': 'network.delete_security_group'},
    'keypair': {'list': 'compute.keypairs', 'delete': 'compute.delete_keypair'},
    'stack': {'list': 'orchestration.stacks', 'delete': 'orchestration.delete_stack'}
}

class ProjectPurge(OpenStackModule):
    argument_spec = dict(
        cloud=dict(type='str', required=True),
        project_name=dict(type='str', required=True),
        keep_project=dict(type='bool', default=False),
        remove_external_networks=dict(type='bool', default=False)
    )

    module_kwargs = dict(
        supports_check_mode=True
    )

    def run(self):
        cloud = self.params['cloud']
        project_name = self.params['project_name']
        keep_project = self.params['keep_project']
        remove_external_networks = self.params['remove_external_networks']

        try:
            conn = self.conn(cloud=cloud)

            project = conn.identity.find_project(project_name)
            if not project:
                self.fail_json(msg=f"Project {project_name} not found")
            project_id = project.id

            if self.ansible.check_mode:
                self.exit_json(changed=True, msg="Project resources would be purged in check mode")

            for resource, handler in RESOURCE_HANDLERS.items():
                resources_info = self.gather_resource_info(conn, resource, project_id, remove_external_networks)
                if resources_info:
                    for res in resources_info:
                        self.log_info(f"Deleting {resource} with ID: {res.id}")
                        self.delete_resource(conn, resource, res)

            if not keep_project:
                try:
                    conn.identity.delete_project(project_id)
                    self.log_info(f"Project {project_name} deleted successfully")
                except openstack_exceptions.ConflictException as e:
                    self.fail_json(msg=f"Failed to delete project {project_name}: {str(e)}")

            self.exit_json(changed=True, msg=f"Project {project_name} purged successfully")

        except Exception as e:
            self.fail_json(msg=str(e))

    def gather_resource_info(self, conn, resource, project_id, remove_external_networks):
        handler = RESOURCE_HANDLERS.get(resource)
        if handler:
            list_method = getattr(conn, handler['list'])
            filters = {'project_id': project_id} if resource != 'keypair' else {'user_id': conn.session.get_project_id()}
            if resource == 'network' and not remove_external_networks:
                filters['router:external'] = False
            return list(list_method(details=True, filters=filters))
        else:
            raise Exception(f"Unsupported resource type: {resource}")

    def delete_resource(self, conn, resource, res):
        handler = RESOURCE_HANDLERS.get(resource)
        if handler:
            delete_method = getattr(conn, handler['delete'])
            if resource == 'port':
                if res.device_owner == 'network:router_interface':
                    try:
                        conn.network.remove_interface_from_router(res.device_id, port_id=res.id)
                        self.log_info(f"Detached port {res.id} from router {res.device_id}")
                    except NetworkNotFound:
                        self.log_warning(f"Router {res.device_id} not found while detaching port {res.id}")
                elif res.device_owner == 'network:router_gateway':
                    conn.network.update_router(res.device_id, external_gateway_info=None)
                elif res.device_owner == 'network:floatingip':
                    floating_ip = conn.network.find_ip(res.fixed_ips[0]['ip_address'])
                    conn.network.update_ip(floating_ip.id, port_id=None)
            if resource == 'router':
                interfaces = conn.network.ports(filters={'device_id': res.id})
                for iface in interfaces:
                    conn.network.remove_interface_from_router(res.id, port_id=iface.id)
                    self.log_info(f"Detached interface {iface.id} from router {res.id}")
            delete_method(res.id)
            self.log_info(f"{resource} with ID: {res.id} deleted successfully")
        else:
            raise Exception(f"Unsupported resource type: {resource}")

if __name__ == '__main__':
    module = ProjectPurge()
    module()
