"""
Infra Model

Este módulo define el modelo de datos del proyecto.

Se encarga de:
1. Representar recursos de infraestructura como objetos Python.
2. Normalizar información obtenida de AWS.
3. Servir como estructura común para análisis, exportación y visualización.

Los extractores obtienen datos de AWS, los convierten a estos modelos y luego el colector los agrupa para que puedan ser utilizados por el sistema.
"""

from dataclasses import dataclass, field
from typing import Optional, Dict, List

@dataclass
class CloudResource:
    resource_id: str
    name: Optional[str] = None
    tags: Optional[Dict[str, str]] = None


@dataclass
class VPC(CloudResource):
    cidr_block: str = ""
    subnets: List["Subnet"] = field(default_factory=list)

@dataclass
class Subnet(CloudResource):
    cidr_block: str = ""
    availability_zone: str = ""
    is_public: bool = False

@dataclass
class SecurityGroupRule:
    protocol: str
    from_port: int
    to_port: int
    cidr_blocks: List[str] = field(default_factory=list)

@dataclass
class SecurityGroup(CloudResource):
    description: Optional[str] = None
    ingress_rules: List[SecurityGroupRule] = field(default_factory=list)
    egress_rules: List[SecurityGroupRule] = field(default_factory=list)

@dataclass
class Instance(CloudResource):
    instance_type: str = ""
    state: str = ""
    vpc_id: str = ""
    subnet_id: str = ""
    security_groups: List[str] = field(default_factory=list)
    public_ip: Optional[str] = None
    private_ip: Optional[str] = None

@dataclass
class InternetGateway(CloudResource):
    vpc_id: str = ""

@dataclass
class NATGateway(CloudResource):
    vpc_id: str = ""
    subnet_id: str = ""
    public_ip: Optional[str] = None
    state: str = ""

@dataclass
class RDSInstance(CloudResource):
    engine: str = ""
    engine_version: str = ""
    instance_class: str = ""
    status: str = ""
    vpc_id: str = ""
    availability_zone: str = ""
    multi_az: bool = False
    publicly_accessible: bool = False
    security_groups: List[str] = field(default_factory=list)

@dataclass
class Route:
    destination: str = ""
    target: str = ""
    state: str = ""

@dataclass
class RouteTable(CloudResource):
    vpc_id: str = ""
    subnet_associations: List[str] = field(default_factory=list)
    routes: List[Route] = field(default_factory=list)
    is_main: bool = False

@dataclass
class Listener:
    port: int = 0
    protocol: str = ""
    target_group_arn: str = ""

@dataclass
class TargetGroup(CloudResource):
    port: int = 0
    protocol: str = ""
    vpc_id: str = ""
    target_type: str = ""
    targets: List[str] = field(default_factory=list)

@dataclass
class LoadBalancer(CloudResource):
    type: str = ""
    scheme: str = ""
    dns_name: str = ""
    vpc_id: str = ""
    availability_zones: List[str] = field(default_factory=list)
    security_groups: List[str] = field(default_factory=list)
    listeners: List[Listener] = field(default_factory=list)

@dataclass
class TGWRoute:
    destination: str = ""
    target_attachment_id: str = ""
    state: str = ""
    route_type: str = ""

@dataclass
class TGWRouteTable(CloudResource):
    tgw_id: str = ""
    routes: List[TGWRoute] = field(default_factory=list)

@dataclass
class TGWAttachment(CloudResource):
    tgw_id: str = ""
    resource_type: str = ""
    resource_id_ref: str = ""
    state: str = ""

@dataclass
class TransitGateway(CloudResource):
    amazon_asn: int = 0
    state: str = ""
    attachments: List[TGWAttachment] = field(default_factory=list)
    route_tables: List[TGWRouteTable] = field(default_factory=list)

@dataclass
class VPNGateway(CloudResource):
    vpc_id: str = ""
    state: str = ""
    amazon_asn: int = 0

@dataclass
class CustomerGateway(CloudResource):
    ip_address: str = ""
    bgp_asn: str = ""
    type: str = ""
    state: str = ""

@dataclass
class VPNConnection(CloudResource):
    vpn_gateway_id: str = ""
    customer_gateway_id: str = ""
    transit_gateway_id: str = ""
    type: str = ""
    state: str = ""
    static_routes_only: bool = False

@dataclass
class ElasticIP(CloudResource):
    public_ip: str = ""
    association_id: str = ""
    instance_id: str = ""
    network_interface_id: str = ""
    domain: str = ""

@dataclass
class VPCPeering(CloudResource):
    requester_vpc_id: str = ""
    requester_cidr: str = ""
    accepter_vpc_id: str = ""
    accepter_cidr: str = ""
    state: str = ""

@dataclass
class DirectConnectConnection(CloudResource):
    bandwidth: str = ""
    location: str = ""
    state: str = ""
    vlan: int = 0

@dataclass
class ECSService:
    service_name: str = ""
    status: str = ""
    desired_count: int = 0
    running_count: int = 0
    launch_type: str = ""
    task_definition: str = ""

@dataclass
class ECSCluster(CloudResource):
    status: str = ""
    registered_instances: int = 0
    running_tasks: int = 0
    pending_tasks: int = 0
    services: List[ECSService] = field(default_factory=list)

@dataclass
class EFSFileSystem(CloudResource):
    size_bytes: int = 0
    performance_mode: str = ""
    lifecycle_state: str = ""
    encrypted: bool = False

@dataclass
class EKSCluster(CloudResource):
    version: str = ""
    status: str = ""
    endpoint: str = ""
    vpc_id: str = ""
    subnet_ids: List[str] = field(default_factory=list)
    security_groups: List[str] = field(default_factory=list)


@dataclass
class InfrastructureData:
    region: str = ""
    vpcs: List[VPC] = field(default_factory=list)
    internet_gateways: List[InternetGateway] = field(default_factory=list)
    nat_gateways: List[NATGateway] = field(default_factory=list)
    security_groups: List[SecurityGroup] = field(default_factory=list)
    instances: List[Instance] = field(default_factory=list)
    rds_instances: List[RDSInstance] = field(default_factory=list)
    route_tables: List[RouteTable] = field(default_factory=list)
    load_balancers: List[LoadBalancer] = field(default_factory=list)
    target_groups: List[TargetGroup] = field(default_factory=list)
    transit_gateways: List[TransitGateway] = field(default_factory=list)
    vpn_gateways: List[VPNGateway] = field(default_factory=list)
    customer_gateways: List[CustomerGateway] = field(default_factory=list)
    vpn_connections: List[VPNConnection] = field(default_factory=list)
    elastic_ips: List[ElasticIP] = field(default_factory=list)
    vpc_peerings: List[VPCPeering] = field(default_factory=list)
    direct_connect_connections: List[DirectConnectConnection] = field(default_factory=list)
    ecs_clusters: List[ECSCluster] = field(default_factory=list)
    efs_file_systems: List[EFSFileSystem] = field(default_factory=list)
    eks_clusters: List[EKSCluster] = field(default_factory=list)


@dataclass
class GeneratedReport:
    documentation: str = ""
    diagram: str = ""
    suggestions: str = ""
