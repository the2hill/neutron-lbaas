# Copyright 2013 New Dream Network, LLC (DreamHost)
# Copyright 2015 Rackspace
#
#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.

from neutron.common import rpc as n_rpc
import oslo_messaging


class LbaasAgentApi(object):
    """Agent side of the Agent to Plugin RPC API."""

    # history
    #   1.0 Initial version

    def __init__(self, topic, context, host):
        self.context = context
        self.host = host
        target = oslo_messaging.Target(topic=topic, version='1.0')
        self.client = n_rpc.get_client(target)

    def get_ready_devices(self):
        cctxt = self.client.prepare()
        return cctxt.call(self.context, 'get_ready_devices', host=self.host)\


    def loadbalancer_deployed(self, load_balancer_id):
        cctxt = self.client.prepare()
        return cctxt.call(self.context, 'loadbalancer_deployed',
                          load_balancer_id=load_balancer_id)

    def update_status(self, obj_type, obj_id, status):
        cctxt = self.client.prepare()
        return cctxt.call(self.context, 'update_status', obj_type=obj_type,
                          obj_id=obj_id, status=status)

    def loadbalancer_destroyed(self, load_balancer_id):
        cctxt = self.client.prepare()
        return cctxt.call(self.context, 'loadbalancer_destroyed',
                          load_balancer_id=load_balancer_id)

    def plug_vip_port(self, port_id):
        cctxt = self.client.prepare()
        return cctxt.call(self.context, 'plug_vip_port', port_id=port_id,
                          host=self.host)

    def unplug_vip_port(self, port_id):
        cctxt = self.client.prepare()
        return cctxt.call(self.context, 'unplug_vip_port', port_id=port_id,
                          host=self.host)

    def update_loadbalancer_stats(self, load_balancer_id, stats):
        cctxt = self.client.prepare()
        return cctxt.call(self.context, 'update_loadbalancer_stats',
                          load_balancer_id=load_balancer_id, stats=stats,
                          host=self.host)