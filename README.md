# AWS Infra Explorer AI

Herramienta interna de Altostratus que analiza automáticamente la infraestructura AWS de cuentas de clientes y genera documentación técnica, sugerencias Well-Architected y diagramas de arquitectura.

---

## Cómo funciona

```
                        ┌─────────────────────────────────────────┐
                        │         AWS Infra Explorer AI            │
                        └─────────────────────────────────────────┘

  ┌──────────┐    HTTPS    ┌─────────────┐    S3 OAC    ┌──────────────────┐
  │ Ingeniero│ ──────────► │ CloudFront  │ ────────────► │  S3 Frontend     │
  │(Browser) │             │   (CDN)     │               │  index.html      │
  └────┬─────┘             └─────────────┘               │  app.js / nav.js │
       │                                                  └──────────────────┘
       │ 1. Login con @altostratus.es
       │ ◄──────────────────────────────────────────── Cognito (JWT)
       │
       │ 2. POST /analyze {account_id, region}
       │ ──────────────────────────────────────────►  API Gateway
       │                                               (valida JWT)
       │                                                    │
       │ 3. 202 {analysis_id}                               ▼
       │ ◄──────────────────────────────────────────── Lambda (sync)
       │                                               auto-invoca async ──►  Lambda (async)
       │                                                                            │
       │                                                              ┌─────────────┼─────────────┐
       │                                                              ▼             ▼             ▼
       │                                                       Cuenta Cliente   Bedrock      S3 Outputs
       │                                                       (AssumeRole)   (Claude S4)  (status.json)
       │                                                       16 extractores  doc + suger.  + archivos
       │
       │ 4. GET /status/{analysis_id}  (polling cada 5s)
       │ ──────────────────────────────────────────────►  API Gateway → Lambda → S3
       │ ◄──────────────────────────────────────────────  {status: "completed", presigned URLs}
       │
       │ 5. Descarga archivos via presigned URLs (1h validez)
       └──────────────────────────────────────────────────────────────────────────────►  S3 Outputs
```

**Pasos del flujo:**

1. El ingeniero abre la URL y se autentica con su cuenta `@altostratus.es`
2. Introduce el Account ID de la cuenta cliente y la región a analizar
3. La Lambda asume el rol `infra-explorer-read-only` en la cuenta cliente via STS
4. Extrae la infraestructura con 16 extractores boto3
5. Genera documentación y sugerencias con Amazon Bedrock (Claude Sonnet 4)
6. Genera un diagrama draw.io con iconos AWS oficiales
7. Sube los outputs a S3 y devuelve presigned URLs al frontend

---

## Infraestructura (Terraform)

Dos stacks independientes para separar lo que cambia frecuentemente de lo que no:

| Stack | Contenido | Frecuencia de cambio |
|---|---|---|
| `terraform/persistent/` | S3 buckets + CloudFront | Rara vez — **NO destruir** |
| `terraform/` | Lambda + API Gateway + IAM + Cognito | Frecuente — destroy/apply sin miedo |

> ⚠️ Al hacer destroy/apply del stack de app, API Gateway se recrea con nueva URL.
> Hay que actualizar `API_URL` en `frontend/app.js` y redesplegar el frontend.

---

## Recursos desplegados

| Recurso | Valor |
|---|---|
| CloudFront | `https://d2y8h0jbecvclg.cloudfront.net` |
| S3 Frontend | `infra-explorer-frontend-sandbox` |
| S3 Outputs | `infra-explorer-outputs-sandbox` (lifecycle 30 días, SSE-S3) |
| API Gateway | `https://gh41sneumj.execute-api.eu-west-1.amazonaws.com` |
| Lambda Analyzer | `infra-explorer-analyzer` |
| Lambda Cognito Trigger | `infra-explorer-cognito-presignup` |
| Cognito User Pool | `eu-west-1_DyJrMHx9N` |
| Cognito Client ID | `1hk5o7m7h2pkvbc5eh79tdgg8n` |
| CloudFront Distribution | `E1MHNIQHI7VQ5F` |

---

## Estructura del proyecto

```
aws-infra-explorer-ai/
├── src/
│   ├── lambda_handler.py          # Entry point Lambda — flujo asíncrono con polling
│   ├── cognito_presignup/
│   │   └── handler.py             # Lambda trigger — bloquea emails no @altostratus.es
│   ├── core/
│   │   ├── orchestrator.py        # Coordina extractores y generadores
│   │   └── session_manager.py     # Gestión sesiones boto3 (AssumeRole)
│   ├── extractors/                # 16 extractores de servicios AWS
│   ├── generators/
│   │   ├── bedrock_generator.py   # Documentación + sugerencias con IA
│   │   └── drawio_generator.py    # Diagramas draw.io (XML)
│   └── models/
│       └── infra_model.py         # Dataclasses de recursos AWS
├── frontend/
│   ├── index.html                 # Shell principal — auth screen + app screen
│   ├── app.js                     # Auth (Cognito) + analizador + polling
│   ├── nav.js                     # Navegación + diagrama canvas
│   └── assets/
│       ├── logo.png
│       └── favicon.ico
├── terraform/
│   ├── persistent/                # S3 + CloudFront — NO destruir
│   │   ├── s3.tf
│   │   ├── cloudfront.tf
│   │   └── outputs.tf
│   ├── iam.tf                     # Roles Lambda + reader + Cognito trigger
│   ├── lambda.tf                  # Lambda analyzer
│   ├── apigateway.tf              # HTTP API + rutas + JWT authorizer Cognito
│   ├── cognito.tf                 # User Pool + App Client
│   ├── cognito_trigger.tf         # Lambda pre-signup + permisos
│   └── outputs.tf
├── scripts/
│   ├── deploy_lambda.sh           # Build zip + update Lambda function code
│   └── deploy_frontend.sh         # S3 sync + CloudFront invalidation
└── prompts/
    ├── documentation_prompt.txt
    └── suggestions_prompt.txt
```

---

## Servicios analizados

| Categoría | Servicios |
|---|---|
| Networking | VPCs, Subnets, IGW, NAT GW, Route Tables, VPC Peering, Elastic IPs |
| Compute | EC2 Instances |
| Containers | ECS Clusters, EKS Clusters |
| Database | RDS Instances |
| Storage | EFS File Systems |
| Load Balancing | ALB, NLB (con Listeners y Target Groups) |
| Connectivity | Transit GW, VPN, Direct Connect |
| Security | Security Groups |

---

## Seguridad

- Sin credenciales estáticas — AssumeRole con credenciales temporales de 1 hora
- JWT Cognito validado por API Gateway antes de llegar a Lambda
- Pre-signup trigger bloquea registros con email que no sea `@altostratus.es`
- S3 outputs privado — acceso solo via presigned URLs (1h validez)
- S3 frontend accesible solo via CloudFront OAC (no público directo)
- Outputs encriptados SSE-S3 (AES256), lifecycle automático de 30 días

---

## Requisitos para el cliente

Crear un rol IAM en la cuenta a analizar:

- **Nombre:** `infra-explorer-read-only`
- **Política:** `ReadOnlyAccess` (AWS managed)
- **Trust Policy:**

```json
{
    "Version": "2012-10-17",
    "Statement": [{
        "Effect": "Allow",
        "Principal": {
            "AWS": "arn:aws:iam::590183851235:role/infra-explorer-lambda-role"
        },
        "Action": "sts:AssumeRole"
    }]
}
```

---

## Perfiles AWS

| Perfil | Uso |
|---|---|
| `sandbox` | Terraform + deploy — AssumeRole `cmc_role_admin` en cuenta `590183851235` |
| `infra-explorer` | Bedrock local (legacy) |

---

## Despliegue

```bash
# Entrar a la sesión AWS (una sola vez por terminal)
aws-vault exec sandbox

# Solo primera vez o cambios en S3/CloudFront
cd terraform/persistent && terraform init && terraform apply

# Lambda + API Gateway + IAM + Cognito
cd terraform && terraform init && terraform apply

# Código Lambda
./scripts/deploy_lambda.sh

# Frontend
./scripts/deploy_frontend.sh
```

---

## Roadmap

| Fase | Descripción | Estado |
|---|---|---|
| 1 | Extracción de infraestructura con boto3 | ✅ |
| 2 | Integración con Amazon Bedrock (Claude Sonnet 4) | ✅ |
| 3 | Error handling y validaciones | ✅ |
| 4 | Servicios expandidos (ELB, TGW, VPN, EIP, DX, ECS, EFS, EKS) | ✅ |
| 5 | Optimización de prompts | ✅ |
| 6 | Diagramas draw.io (XML programático) | ✅ |
| 7 | Refactor: sesión boto3 inyectable + paginación | ✅ |
| 8 | Despliegue serverless (Terraform + Lambda + CloudFront) | ✅ |
| 9 | Autenticación (Amazon Cognito) | ✅ |
| 10 | Historial de análisis compartido | ⬜ Pendiente |
| 11 | Pestañas en diagrama draw.io por categoría | ⬜ Pendiente |
| 12 | Dominio personalizado (Route 53 + ACM) | ⬜ Pendiente |
