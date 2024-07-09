#!/usr/bin/python

from ansible_collections.openstack.cloud.plugins.module_utils.openstack import OpenStackModule
from openstack import exceptions as openstack_exceptions

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
    'floating_ip': {'list': lambda conn, filters: conn.network.ips(details=True, **filters),
                    'delete': lambda conn, resource_id: conn.network.delete_ip(resource_id)},
    'router': {'list': lambda conn, filters: conn.search_routers(**filters),
               'delete': lambda conn, resource_id: conn.network.delete_router(resource_id)},
    'snapshot': {'list': lambda conn, filters: conn.block_storage.snapshots(details=True, **filters),
                 'delete': lambda conn, resource_id: conn.block_storage.delete_snapshot(resource_id)},
    'volume': {'list': lambda conn, filters: conn.block_storage.volumes(details=True, **filters),
               'delete': lambda conn, resource_id: conn.block_storage.delete_volume(resource_id)},
    'server': {'list': lambda conn, filters: conn.compute.servers(details=True, **filters),
               'delete': lambda conn, resource_id: conn.compute.delete_server(resource_id)},
    'port': {'list': lambda conn, filters: conn.network.ports(details=True, **filters),
             'delete': lambda conn, resource_id: conn.network.delete_port(resource_id)},
    'subnet': {'list': lambda conn, filters: conn.network.subnets(details=True, **filters),
               'delete': lambda conn, resource_id: conn.network.delete_subnet(resource_id)},
    'network': {'list': lambda conn, filters: conn.network.networks(details=True, **filters),
                'delete': lambda conn, resource_id: conn.network.delete_network(resource_id)},
    'image': {'list': lambda conn, filters: conn.image.images(details=True, **filters),
              'delete': lambda conn, resource_id: conn.image.delete_image(resource_id)},
    'security_group': {'list': lambda conn, filters: conn.network.security_groups(details=True, **filters),
                       'delete': lambda conn, resource_id: conn.network.delete_security_group(resource_id)},
    'keypair': {'list': lambda conn, filters: conn.compute.keypairs(details=True, **filters),
                'delete': lambda conn, resource_id: conn.compute.delete_keypair(resource_id)},
    'stack': {'list': lambda conn, filters: conn.orchestration.stacks(details=True, **filters),
              'delete': lambda conn, resource_id: conn.orchestration.delete_stack(resource_id)},
}


class ProjectPurge(OpenStackModule):
    argument_spec = dict(
        project=dict(required=True),
        keep_project=dict(type='bool', default=False),
        remove_external_networks=dict(type='bool', default=False)
    )

    module_kwargs = dict(
        supports_check_mode=True
    )

    def run(self):
        # parse the parameters
        project = self.params['project']
        keep_project = self.params['keep_project']
        remove_external_networks = self.params['remove_external_networks']

        # seed the results dict in the object
        self.results = dict(
            changed=False,
            messages=[]
        )

        try:
            proj = self.conn.identity.find_project(project)
            if not project:
                self.fail(msg=f"Project {project} not found",
                          **self.results)
            project_id = proj.id

            if self.ansible.check_mode:
                self.results['changed'] = False
                self.exit(msg="Check mode: Project resources would be purged.",
                          **self.results)

            for resource, handler in RESOURCE_HANDLERS.items():
                resources_info = self.gather_resource_info(resource,
                                                           project_id,
                                                           remove_external_networks)
                if resources_info:
                    for res in resources_info:
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
            self.exit(msg=f"Project {project} purged successfully",
                      **self.results)

        except Exception as e:
            self.fail(msg=str(e), **self.results)

    def gather_resource_info(self, resource, project_id, remove_external_networks):
        handler = RESOURCE_HANDLERS.get(resource)
        if handler:
            list_method = handler['list']
            filters = {'project_id': project_id} if resource != 'keypair' else {
                'user_id': self.conn.session.get_project_id()}
            if resource == 'network' and not remove_external_networks:
                filters['router:external'] = False
            return list(list_method(self.conn, filters=filters))
        else:
            raise Exception(f"Unsupported resource type: {resource}")

    def delete_resource(self, resource, res):
        handler = RESOURCE_HANDLERS.get(resource)
        if handler:
            delete_method = handler['delete']
            if resource == 'port':
                if res.device_owner == 'network:router_interface':
                    try:
                        self.conn.network.remove_interface_from_router(
                            res.device_id, port_id=res.id)
                        self.log(
                            f"Detached port {res.id} from router {res.device_id}")
                    except NetworkNotFound:
                        self.log_warning(
                            f"Router {res.device_id} not found while detaching port {res.id}")
                elif res.device_owner == 'network:router_gateway':
                    self.conn.network.update_router(
                        res.device_id, external_gateway_info=None)
                elif res.device_owner == 'network:floatingip':
                    floating_ip = self.conn.network.find_ip(
                        res.fixed_ips[0]['ip_address'])
                    self.conn.network.update_ip(floating_ip.id, port_id=None)
            if resource == 'router':
                interfaces = self.conn.network.ports(
                    filters={'device_id': res.id})
                for iface in interfaces:
                    self.conn.network.remove_interface_from_router(
                        res.id, port_id=iface.id)
                    self.log(
                        f"Detached interface {iface.id} from router {res.id}")
            delete_method(self.conn, res.id)
            self.log(f"{resource} with ID: {res.id} deleted successfully")
        else:
            raise Exception(f"Unsupported resource type: {resource}")

    def log(self, msg):
        """Prints log message to system log.

        Arguments:
            msg {str} -- Log message
        """
        self.results['messages'].append(msg)
        self.ansible.log(msg)


if __name__ == '__main__':
    module = ProjectPurge()
    module()
