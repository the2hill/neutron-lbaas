# Copyright (c) 2014 OpenStack Foundation.
# All Rights Reserved.
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
"""
This module holds the data models for the load balancer service plugin.  These
are meant simply as replacement data structures for dictionaries and
SQLAlchemy models.  Using dictionaries as data containers for many components
causes readability issues and does not intuitively give the benefits of what
classes and OO give.  Using SQLAlchemy models as data containers for many
components can become an issue if you do not want to give certain components
access to the database.

These data models do provide methods for instantiation from SQLAlchemy models
and also converting to dictionaries.
"""

from neutron.db import model_base
from neutron.db import models_v2
from neutron.db import servicetype_db
from sqlalchemy.orm import collections

from neutron_lbaas.db.loadbalancer import models


class BaseDataModel(object):

    # NOTE(brandon-logan) This does not yet discover dicts for relationship
    # attributes.
    def to_dict(self, _from_id=None, **kwargs):
        ret = {}
        # if _from_id and hasattr(self, 'id') and self.id == _from_id:
        #     return None
        for attr in self.__dict__:
            if attr.startswith('_') or not kwargs.get(attr, True):
                continue
            if isinstance(getattr(self, attr), list):
                ret[attr] = []
                for item in self.__dict__[attr]:
                    if isinstance(item, BaseDataModel):
                        # if (_from_id and hasattr(item, 'id') and
                        #             item.id == _from_id):
                        #     continue
                        ret[attr] = item.to_dict()
                    else:
                        ret[attr] = item
            elif isinstance(getattr(self, attr), BaseDataModel):
                ret[attr] = self.__dict__[attr].to_dict()
            elif isinstance(self.__dict__[attr], unicode):
                ret[attr.encode('utf8')] = self.__dict__[attr].encode('utf8')
            else:
                ret[attr] = self.__dict__[attr]
        return ret

    def to_api_dict(self, **kwargs):
        return {}

    @classmethod
    def from_sqlalchemy_model(cls, sa_model, calling_class=None):
        instance = cls()
        for attr_name in vars(instance):
            if attr_name.startswith('_'):
                continue
            attr = getattr(sa_model, attr_name)
            # Handles M:1 or 1:1 relationships
            if isinstance(attr, model_base.BASEV2):
                if hasattr(instance, attr_name):
                    data_class = SA_MODEL_TO_DATA_MODEL_MAP[attr.__class__]
                    if calling_class != data_class and data_class:
                        setattr(instance, attr_name,
                                data_class.from_sqlalchemy_model(
                                    attr, calling_class=cls))
            # Handles 1:M or M:M relationships
            elif isinstance(attr, collections.InstrumentedList):
                for item in attr:
                    if hasattr(instance, attr_name):
                        data_class = SA_MODEL_TO_DATA_MODEL_MAP[item.__class__]
                        attr_list = getattr(instance, attr_name) or []
                        attr_list.append(data_class.from_sqlalchemy_model(
                            item, calling_class=cls))
                        setattr(instance, attr_name, attr_list)
            # This isn't a relationship so it must be a "primitive"
            else:
                setattr(instance, attr_name, getattr(sa_model, attr_name))
        return instance

    @property
    def root_loadbalancer(self):
        """Returns the loadbalancer this instance is attached to."""
        if isinstance(self, LoadBalancer):
            lb = self
        elif isinstance(self, Listener):
            lb = self.loadbalancer
        elif isinstance(self, Pool):
            lb = self.listener.loadbalancer
        else:
            # Pool Member or Health Monitor
            lb = self.pool.listener.loadbalancer
        return lb


# NOTE(brandon-logan) IPAllocation, Port, and ProviderResourceAssociation are
# defined here because there aren't any data_models defined in core neutron
# or neutron services.  Instead of jumping through the hoops to create those
# I've just defined them here.  If ever data_models or similar are defined
# in those packages, those should be used instead of these.
class IPAllocation(BaseDataModel):

    def __init__(self, port_id=None, ip_address=None, subnet_id=None,
                 network_id=None):
        self.port_id = port_id
        self.ip_address = ip_address
        self.subnet_id = subnet_id
        self.network_id = network_id


class Port(BaseDataModel):

    def __init__(self, id=None, tenant_id=None, name=None, network_id=None,
                 mac_address=None, admin_state_up=None, status=None,
                 device_id=None, device_owner=None, fixed_ips=None):
        self.id = id
        self.tenant_id = tenant_id
        self.name = name
        self.network_id = network_id
        self.mac_address = mac_address
        self.admin_state_up = admin_state_up
        self.status = status
        self.device_id = device_id
        self.device_owner = device_owner
        self.fixed_ips = fixed_ips or []


class ProviderResourceAssociation(BaseDataModel):

    def __init__(self, provider_name=None, resource_id=None):
        self.provider_name = provider_name
        self.resource_id = resource_id


class SessionPersistence(BaseDataModel):

    def __init__(self, pool_id=None, type=None, cookie_name=None,
                 pool=None):
        self.pool_id = pool_id
        self.type = type
        self.cookie_name = cookie_name
        self.pool = pool

    def to_api_dict(self):
        return super(SessionPersistence, self).to_dict(pool=False,
                                                       pool_id=False)


class LoadBalancerStatistics(BaseDataModel):

    def __init__(self, loadbalancer_id=None, bytes_in=None, bytes_out=None,
                 active_connections=None, total_connections=None,
                 loadbalancer=None):
        self.loadbalancer_id = loadbalancer_id
        self.bytes_in = bytes_in
        self.bytes_out = bytes_out
        self.active_connections = active_connections
        self.total_connections = total_connections
        self.loadbalancer = loadbalancer

    def to_api_dict(self):
        return super(LoadBalancerStatistics, self).to_dict(
            loadbalancer_id=False, loadbalancer=False)


class HealthMonitor(BaseDataModel):

    def __init__(self, id=None, tenant_id=None, type=None, delay=None,
                 timeout=None, max_retries=None, http_method=None,
                 url_path=None, expected_codes=None, provisioning_status=None,
                 admin_state_up=None, pool=None):
        self.id = id
        self.tenant_id = tenant_id
        self.type = type
        self.delay = delay
        self.timeout = timeout
        self.max_retries = max_retries
        self.http_method = http_method
        self.url_path = url_path
        self.expected_codes = expected_codes
        self.provisioning_status = provisioning_status
        self.admin_state_up = admin_state_up
        self.pool = pool

    def attached_to_loadbalancer(self):
        return bool(self.pool and self.pool.listener and
                    self.pool.listener.loadbalancer)

    def to_api_dict(self):
        ret_dict = super(HealthMonitor, self).to_dict(
            provisioning_status=False, pool=False)
        ret_dict['pools'] = []
        if self.pool:
            ret_dict['pools'].append({'id': self.pool.id})
        return ret_dict


class Pool(BaseDataModel):

    def __init__(self, id=None, tenant_id=None, name=None, description=None,
                 healthmonitor_id=None, protocol=None, lb_algorithm=None,
                 admin_state_up=None, operating_status=None,
                 provisioning_status=None, members=None, healthmonitor=None,
                 sessionpersistence=None, listener=None):
        self.id = id
        self.tenant_id = tenant_id
        self.name = name
        self.description = description
        self.healthmonitor_id = healthmonitor_id
        self.protocol = protocol
        self.lb_algorithm = lb_algorithm
        self.admin_state_up = admin_state_up
        self.operating_status = operating_status
        self.provisioning_status = provisioning_status
        self.members = members or []
        self.healthmonitor = healthmonitor
        self.sessionpersistence = sessionpersistence
        self.listener = listener

    def attached_to_loadbalancer(self):
        return bool(self.listener and self.listener.loadbalancer)

    def to_api_dict(self):
        ret_dict = super(Pool, self).to_dict(
            provisioning_status=False, operating_status=False,
            healthmonitor=False, listener=False, session_persistence=False)
        # NOTE(blogan): Returning a list to future proof for M:N objects
        # that are not yet implemented.
        ret_dict['listeners'] = []
        if self.listener:
            ret_dict['listeners'].append({'id': self.listener.id})
        ret_dict['session_persistence'] = None
        if self.sessionpersistence:
            ret_dict['session_persistence'] = (
                self.sessionpersistence.to_api_dict())
        ret_dict['members'] = [{'id': member.id} for member in self.members]
        return ret_dict


class Member(BaseDataModel):

    def __init__(self, id=None, tenant_id=None, pool_id=None, address=None,
                 protocol_port=None, weight=None, admin_state_up=None,
                 subnet_id=None, operating_status=None,
                 provisioning_status=None, pool=None):
        self.id = id
        self.tenant_id = tenant_id
        self.pool_id = pool_id
        self.address = address
        self.protocol_port = protocol_port
        self.weight = weight
        self.admin_state_up = admin_state_up
        self.subnet_id = subnet_id
        self.operating_status = operating_status
        self.provisioning_status = provisioning_status
        self.pool = pool

    def attached_to_loadbalancer(self):
        return bool(self.pool and self.pool.listener and
                    self.pool.listener.loadbalancer)

    def to_api_dict(self):
        return super(Member, self).to_dict(
            provisioning_status=False, operating_status=False, pool=False)


class Listener(BaseDataModel):

    def __init__(self, id=None, tenant_id=None, name=None, description=None,
                 default_pool_id=None, loadbalancer_id=None, protocol=None,
                 protocol_port=None, connection_limit=None,
                 admin_state_up=None, provisioning_status=None,
                 operating_status=None, default_pool=None, loadbalancer=None):
        self.id = id
        self.tenant_id = tenant_id
        self.name = name
        self.description = description
        self.default_pool_id = default_pool_id
        self.loadbalancer_id = loadbalancer_id
        self.protocol = protocol
        self.protocol_port = protocol_port
        self.connection_limit = connection_limit
        self.admin_state_up = admin_state_up
        self.operating_status = operating_status
        self.provisioning_status = provisioning_status
        self.default_pool = default_pool
        self.loadbalancer = loadbalancer

    def attached_to_loadbalancer(self):
        return bool(self.loadbalancer)

    def to_api_dict(self):
        ret_dict = super(Listener, self).to_dict(
            loadbalancer=False, loadbalancer_id=False, default_pool=False,
            operating_status=False, provisioning_status=False)
        # NOTE(blogan): Returning a list to future proof for M:N objects
        # that are not yet implemented.
        ret_dict['loadbalancers'] = []
        if self.loadbalancer:
            ret_dict['loadbalancers'].append({'id': self.loadbalancer.id})
        return ret_dict


class LoadBalancer(BaseDataModel):

    def __init__(self, id=None, tenant_id=None, name=None, description=None,
                 vip_subnet_id=None, vip_port_id=None, vip_address=None,
                 provisioning_status=None, operating_status=None,
                 admin_state_up=None, vip_port=None, stats=None,
                 provider=None, listeners=None):
        self.id = id
        self.tenant_id = tenant_id
        self.name = name
        self.description = description
        self.vip_subnet_id = vip_subnet_id
        self.vip_port_id = vip_port_id
        self.vip_address = vip_address
        self.operating_status = operating_status
        self.provisioning_status = provisioning_status
        self.admin_state_up = admin_state_up
        self.vip_port = vip_port
        self.stats = stats
        self.provider = provider
        self.listeners = listeners or []

    def attached_to_loadbalancer(self):
        return True

    def to_api_dict(self):
        ret_dict = super(LoadBalancer, self).to_dict(
            vip_port=False, stats=False, listeners=False)
        ret_dict['listeners'] = [{'id': listener.id}
                                 for listener in self.listeners]
        if self.provider:
            ret_dict['provider'] = self.provider.provider_name
        return ret_dict


SA_MODEL_TO_DATA_MODEL_MAP = {
    models.LoadBalancer: LoadBalancer,
    models.HealthMonitorV2: HealthMonitor,
    models.Listener: Listener,
    models.PoolV2: Pool,
    models.MemberV2: Member,
    models.LoadBalancerStatistics: LoadBalancerStatistics,
    models.SessionPersistenceV2: SessionPersistence,
    models_v2.IPAllocation: IPAllocation,
    models_v2.Port: Port,
    servicetype_db.ProviderResourceAssociation: ProviderResourceAssociation
}

DATA_MODEL_TO_SA_MODEL_MAP = {
    LoadBalancer: models.LoadBalancer,
    HealthMonitor: models.HealthMonitorV2,
    Listener: models.Listener,
    Pool: models.PoolV2,
    Member: models.MemberV2,
    LoadBalancerStatistics: models.LoadBalancerStatistics,
    SessionPersistence: models.SessionPersistenceV2,
    IPAllocation: models_v2.IPAllocation,
    Port: models_v2.Port,
    ProviderResourceAssociation: servicetype_db.ProviderResourceAssociation
}
