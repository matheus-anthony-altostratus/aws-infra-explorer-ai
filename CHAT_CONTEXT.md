# AWS Infra Explorer AI — Contexto para nuevo chat

## Reglas del chat

1. **NO modificar archivos directamente.** El modo agentic-coding está OFF. Solo proporcionar fragmentos exactos (buscar → reemplazar) para que el usuario copie y pegue manualmente.
2. **Idioma:** Español siempre.
3. **Formato de instrucciones:** Fragmento exacto a buscar (copyable) + reemplazo completo + indicar en qué archivo y dónde ponerlo.
4. **Mínimo código:** Solo lo estrictamente necesario. Sin verbosidad.
5. **InfrastructureData es un dataclass**, NO un dict. Usar acceso por atributos (ej: `infra.security_groups`, `sg.ingress_rules`, `rule.cidr_blocks`), nunca `.get()`.
6. **Deploy scripts:** `./scripts/deploy_lambda.sh` (zip + update Lambda) y `./scripts/deploy_frontend.sh` (S3 sync + CloudFront invalidation). Terraform con `aws-vault exec sandbox`.
7. El proyecto está en `/Users/anthonymatheus/Documents/Altostratus/Documents/aws-infra-explorer-ai`

---

## Descripción del proyecto

Herramienta interna de **Altostratus** (equipo CMC-AWS) que analiza automáticamente la infraestructura AWS de cuentas de clientes y genera:
- `infra_{region}.json` — inventario de recursos
- `documentation_{region}.md` — documentación técnica (Bedrock Claude Sonnet 4)
- `suggestions_{region}.md` — sugerencias Well-Architected (5 pilares)
- `diagram_{region}.drawio` — diagrama con 8 pestañas + iconos AWS oficiales

**Problema que resuelve:** Muchos clientes tienen 10+ cuentas con Organizations/Identity Center. El conocimiento de la infraestructura vive solo en la cabeza de los ingenieros. Esta herramienta genera documentación automática en minutos sin credenciales estáticas.

---

## Arquitectura AWS

```
Browser → CloudFront (OAC) → S3 Frontend
Browser → Cognito (JWT) → API Gateway HTTP → Lambda (router)
Lambda → STS AssumeRole → Cuenta Cliente (infra-explorer-read-only)
Lambda → Bedrock (Claude Sonnet 4) → docs + sugerencias
Lambda → S3 Outputs (presigned URLs 1h)
Lambda → DynamoDB (accounts + history)
```

---

## Recursos desplegados

| Recurso | Valor |
|---|---|
| CloudFront URL | `https://d2y8h0jbecvclg.cloudfront.net` |
| S3 Frontend | `infra-explorer-frontend-sandbox` |
| S3 Outputs | `infra-explorer-outputs-sandbox` |
| API Gateway | `https://gh41sneumj.execute-api.eu-west-1.amazonaws.com` |
| Lambda Analyzer | `infra-explorer-analyzer` |
| Lambda Cognito Trigger | `infra-explorer-cognito-presignup` |
| Cognito User Pool | `eu-west-1_DyJrMHx9N` |
| Cognito Client ID | `1hk5o7m7h2pkvbc5eh79tdgg8n` |
| DynamoDB Accounts | `infra-explorer-accounts` |
| DynamoDB History | `infra-explorer-history` |

---

## Estructura del proyecto

```
aws-infra-explorer-ai/
├── src/
│   ├── lambda_handler.py          # Router HTTP + análisis asíncrono + CRUD + dashboard + alerts
│   ├── cognito_presignup/handler.py
│   ├── core/
│   │   ├── orchestrator.py
│   │   └── session_manager.py
│   ├── extractors/                # 19 extractores boto3
│   ├── generators/
│   │   ├── bedrock_generator.py
│   │   ├── drawio_generator.py
│   │   └── notion_generator.py
│   ├── models/
│   │   └── infra_model.py         # Dataclasses (InfrastructureData, SecurityGroup, Instance, etc.)
│   └── prompts/
├── frontend/
│   ├── index.html                 # Auth + App (sidebar + secciones)
│   ├── app.js                     # Auth (Cognito) + analizador + cuentas + usuarios + dashboard + alerts
│   ├── nav.js                     # navigate() + drawArchDiagram()
│   └── assets/
├── terraform/
│   ├── persistent/                # S3 + CloudFront — NO destruir
│   ├── iam.tf                     # Roles Lambda + Cognito admin
│   ├── lambda.tf
│   ├── apigateway.tf              # HTTP API + rutas + JWT authorizer
│   ├── cognito.tf                 # User Pool (allow_admin_create_user_only = true)
│   ├── cognito_trigger.tf
│   ├── dynamodb.tf
│   └── outputs.tf
└── scripts/
    ├── deploy_lambda.sh
    └── deploy_frontend.sh
```

---

## Endpoints API Gateway

| Método | Ruta | Función |
|---|---|---|
| POST | /analyze | Lanza análisis asíncrono |
| GET | /status/{analysis_id} | Polling de status |
| GET | /download/{analysis_id}/{filename} | Redirect presigned URL |
| GET | /history | Historial agrupado |
| GET | /accounts | Listar cuentas |
| POST | /accounts | Crear cuenta |
| PUT | /accounts/{group_id}/{account_id} | Actualizar cuenta |
| DELETE | /accounts/{group_id}/{account_id} | Eliminar cuenta |
| GET | /profiles/{group_id} | Leer Service Profile |
| PUT | /profiles/{group_id} | Guardar Service Profile |
| POST | /notion/{s3_prefix} | Publicar en Notion |
| GET | /dashboard | Panel operativo (métricas + clientes + scores) |
| GET | /alerts | Todas las alertas consolidadas |
| GET | /users | Listar usuarios Cognito |
| POST | /users | Crear usuario (AdminCreateUser) |
| DELETE | /users/{email} | Eliminar usuario |
| POST | /users/{email}/reset | Reset password |
| GET | /users/log | Audit log de acciones de usuario |

---

## Frontend — Secciones

| Sección | Contenido |
|---|---|
| **Dashboard (home)** | Tabs: [📊 Resumen] [🚨 Alertas]. Resumen: métricas + tabla clientes con Health Score + leyenda colapsable + diagrama arquitectura. Alertas: tabla acordeón agrupada por cuenta, filtrable por severidad/cuenta. |
| **Cuentas** | CRUD de cuentas AWS agrupadas por cliente + Service Profile modal |
| **Analizador** | Formulario (cuenta + región) → polling → resultados (docs/sugerencias + descargas) |
| **Historial** | Análisis agrupados por cuenta, expandibles |
| **Usuarios** | Lista Cognito + crear/eliminar/reset + audit log |
| **Guía** | Pasos para crear rol `infra-explorer-read-only` en cuenta cliente |

---

## Fases completadas

| # | Fase | Estado |
|---|---|---|
| 1 | Extracción de infraestructura con boto3 (19 extractores) | ✅ |
| 2 | Integración con Amazon Bedrock (Claude Sonnet 4) | ✅ |
| 3 | Error handling y validaciones | ✅ |
| 4 | Servicios expandidos (ELB, TGW, VPN, EIP, DX, ECS, EFS, EKS) | ✅ |
| 5 | Optimización de prompts | ✅ |
| 6 | Diagramas draw.io (XML programático, 8 pestañas) | ✅ |
| 7 | Refactor: sesión boto3 inyectable + paginación | ✅ |
| 8 | Despliegue serverless (Terraform + Lambda + CloudFront) | ✅ |
| 9 | Autenticación (Amazon Cognito) | ✅ |
| 10 | Historial + gestión de cuentas (DynamoDB) | ✅ |
| 11 | Diagrama draw.io 8 pestañas + extractores DynamoDB e IAM | ✅ |
| 12 | Service Profile — ficha técnica y runbook por cliente | ✅ |
| 13 | Gestión de usuarios — admin-only + auditoría | ✅ |
| 14 | Health Score — puntuación automática de seguridad | ✅ |
| 15 | Dashboard operativo — panel de estado de todos los clientes | ✅ |
| 16 | Alertas de seguridad — detección de configuraciones peligrosas | ✅ |

---

## Fase 16 — Detalle de implementación (última completada)

### Backend (`lambda_handler.py`)

- **`_generate_security_alerts(infra)`** — función separada que analiza la infraestructura y devuelve lista de alertas con: `severity` (critical/high/medium/low/info), `resource`, `type`, `msg`
- **Reglas de detección:**
  - SG con 0.0.0.0/0 en puertos 22/3389 → critical
  - SG con todos los puertos abiertos → critical
  - SG con puertos BD abiertos (3306, 5432, etc.) → high
  - SG con cualquier puerto público → high
  - SG con rango amplio (>100 puertos) → medium
  - RDS públicamente accesible → critical
  - RDS sin Multi-AZ → high
  - Single NAT GW por VPC → medium
  - EC2 stopped → medium
  - IAM users sin MFA → high
  - EIP sin asociar → low
  - EC2 sin tag Name → info
- **`_calculate_health_score(infra)`** — usa `_generate_security_alerts` y aplica penalizaciones: critical=15, high=10, medium=5, low=3, info=2
- **`GET /alerts`** — lee status.json de cada cuenta, consolida alertas, ordena por severidad

### Frontend

- **Dashboard con tabs:** `[📊 Resumen] [🚨 Alertas]`
- **Pestaña Alertas:** acordeón agrupado por cuenta (click para expandir/colapsar), tabla con severidad/tipo/recurso/descripción, filtros por severidad y cuenta
- **Card "Alertas activas"** clickable → abre pestaña alertas
- Funciones: `switchDashboardTab()`, `loadAlerts()`, `filterAlerts()`, `renderAlerts()`, `populateAlertAccountFilter()`

---

## Fase 17 — Comparación entre análisis (Diff) — SIGUIENTE

**Estado:** Por implementar

**Concepto:** Detectar qué cambió en la infraestructura entre el análisis actual y el anterior.

**Decisión pendiente:** Dónde mostrar el diff:
- **Opción A:** Tercera pestaña en Dashboard `[📊 Resumen] [🚨 Alertas] [🔄 Cambios]`
- **Opción B:** Tab adicional en los resultados del análisis (cuando se completa)
- **Opción C:** Ambas

**Categorías del diff:**
- 🟢 Nuevo — recursos que no existían
- 🔴 Eliminado — recursos que desaparecieron
- 🟡 Modificado — recursos que cambiaron propiedades

**Enfoque técnico probable:**
- Antes de sobreescribir `infra_{region}.json` en S3, leer el anterior
- Comparar recurso por recurso (por `resource_id`)
- Guardar diff en status.json o archivo separado
- Frontend muestra diff con visual claro

---

## Fases futuras (roadmap)

| # | Fase | Estado |
|---|---|---|
| 17 | Comparación entre análisis (Diff) | 🔧 Siguiente |
| 18 | Análisis multi-región | ⬜ Futuro |
| 19 | Integración con Notion — publicar automáticamente | ⬜ Futuro |
| 20 | Exportar a PDF con branding Altostratus | ⬜ Futuro |
| 21 | Métricas de uso del equipo | ⬜ Futuro |
| 22 | Resumen semanal automatizado (email) | ⬜ Futuro |
| 23 | Chatbot sobre infraestructura (Bedrock + RAG) | ⬜ Futuro |
| 24 | Integración con ServiceNow (tickets desde alertas) | ⬜ Futuro |
| 25 | Dominio personalizado (Route 53 + ACM) | ⬜ Futuro |

---

## Modelo de datos clave (`src/models/infra_model.py`)

```python
@dataclass
class InfrastructureData:
    region: str
    vpcs: List[VPC]                          # VPC.resource_id, .name, .cidr_block, .subnets
    security_groups: List[SecurityGroup]      # SG.ingress_rules → SecurityGroupRule(.from_port, .to_port, .cidr_blocks)
    instances: List[Instance]                 # EC2.state, .name, .instance_type, .vpc_id
    rds_instances: List[RDSInstance]          # .publicly_accessible, .multi_az, .engine
    nat_gateways: List[NATGateway]           # .vpc_id, .state
    elastic_ips: List[ElasticIP]             # .association_id, .public_ip
    load_balancers: List[LoadBalancer]       # .type, .scheme, .listeners
    transit_gateways: List[TransitGateway]
    vpn_connections: List[VPNConnection]
    ecs_clusters: List[ECSCluster]
    eks_clusters: List[EKSCluster]
    efs_file_systems: List[EFSFileSystem]
    dynamodb_tables: List[DynamoDBTable]
    iam_summary: IAMSummary                  # .users → IAMUser(.mfa_active, .username)
    # ... más campos
```

---

## Notas técnicas importantes

- **Terraform:** Dos stacks separados. `terraform/persistent/` (S3 + CloudFront, NO destruir) y `terraform/` (Lambda + API GW + IAM + Cognito + DynamoDB, destroy/apply sin miedo).
- **Al hacer destroy/apply del stack app:** API Gateway se recrea con nueva URL → actualizar `API_URL` en `frontend/app.js` y redesplegar frontend.
- **DynamoDB history:** Se usa también para audit log de usuarios con `analysis_id = "USER_ACTION#uuid"`.
- **S3 outputs:** Cada análisis sobreescribe la carpeta `{account_id}_{region}/` (no se acumulan versiones). Lifecycle 30 días.
- **Auth:** `allow_admin_create_user_only = true` en Cognito. Solo usuarios existentes pueden crear nuevos via AdminCreateUser. Pre-signup trigger bloquea emails no @altostratus.es.
- **Perfil AWS:** `sandbox` → AssumeRole `cmc_role_admin` en cuenta `590183851235`.
