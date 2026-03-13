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
