# AWS Infra Explorer AI

Herramienta interna de Altostratus que analiza automáticamente la infraestructura AWS de clientes y genera:

- Documentación técnica detallada (Markdown, generada con Amazon Bedrock - Claude Sonnet 4)
- Sugerencias de mejora basadas en AWS Well-Architected Framework
- Diagramas de arquitectura profesionales (draw.io con iconos AWS)

---

## Arquitectura
┌─────────────────────────────────────────────────────────────┐
│ Ingeniero abre https://d2y8h0jbecvclg.cloudfront.net │
└──────────────┬──────────────────────────────────────────────┘
│
┌──────────────▼──────────────────────────────────────────────┐
│ CloudFront (CDN + HTTPS) │
│ ├── /* → S3 Frontend (HTML/CSS/JS) │
│ └── /analyze, /download → API Gateway → Lambda │
└──────────────┬──────────────────────────────────────────────┘
│
┌──────────────▼──────────────────────────────────────────────┐
│ Lambda (Python 3.12, 1024MB, 10min timeout) │
│ ├── STS AssumeRole → cuenta del cliente (ReadOnlyAccess) │
│ ├── 16 extractores boto3 (VPC, EC2, RDS, ECS, EKS, etc.) │
│ ├── Amazon Bedrock (Claude Sonnet 4) → doc + sugerencias │
│ ├── draw.io generator (XML programático) │
│ └── Upload outputs → S3 (presigned URLs) │
└─────────────────────────────────────────────────────────────┘


---

## Infraestructura (Terraform)

La infraestructura está dividida en dos stacks independientes:

| Stack | Contenido | Frecuencia de cambio |
|---|---|---|
| `terraform/persistent/` | S3 buckets + CloudFront | Rara vez (no se destruye) |
| `terraform/app/` | Lambda + API Gateway + IAM | Frecuente (destroy/apply sin miedo) |

### Recursos desplegados

| Recurso | Nombre/URL |
|---|---|
| CloudFront | `https://d2y8h0jbecvclg.cloudfront.net` |
| S3 Frontend | `infra-explorer-frontend-sandbox` |
| S3 Outputs | `infra-explorer-outputs-sandbox` (lifecycle 30 días) |
| API Gateway | `https://gdz678r5rl.execute-api.eu-west-1.amazonaws.com` |
| Lambda | `infra-explorer-analyzer` |

---

## Perfiles AWS

| Perfil | Uso | Permisos |
|---|---|---|
| `sandbox` | Terraform + deploy (cuenta sandbox vía cuenta de salto) | cmc_role_admin |
| `infra-explorer` | Bedrock (solo ejecución local) | Usuario IAM en sandbox |

---

### Requisitos

- Terraform >= 1.5
- AWS CLI v2
- aws-vault configurado con perfil `sandbox`

### Infraestructura (solo la primera vez o al cambiar infra)

```bash
# Stack persistente (S3 + CloudFront)
cd terraform/persistent
aws-vault exec sandbox -- terraform init
aws-vault exec sandbox -- terraform apply

# Stack de aplicación (Lambda + API Gateway + IAM)
cd terraform/app
aws-vault exec sandbox -- terraform init
aws-vault exec sandbox -- terraform apply


Copy

Insert at cursor
Deploy Lambda (código backend)
aws-vault exec sandbox -- ./scripts/deploy_lambda.sh

Copy

Insert at cursor
bash
Deploy Frontend
aws-vault exec sandbox -- ./scripts/deploy_frontend.sh

Copy

Insert at cursor
bash
Estructura del Proyecto
aws-infra-explorer-ai/
│
├── src/                              # Código fuente
│   ├── lambda_handler.py             # Entry point Lambda (API Gateway)
│   ├── core/
│   │   ├── orchestrator.py           # Coordina extractores y generadores
│   │   └── session_manager.py        # Gestión de sesiones boto3 (AssumeRole)
│   ├── extractors/                   # 16 extractores de servicios AWS
│   ├── generators/
│   │   ├── bedrock_generator.py      # Documentación + sugerencias con IA
│   │   └── drawio_generator.py       # Diagramas draw.io (XML)
│   ├── models/
│   │   └── infra_model.py            # Dataclasses de recursos AWS
│   └── web/                          # Interfaz web local (FastAPI, legacy)
│
├── frontend/                         # Frontend estático (CloudFront + S3)
│   ├── index.html
│   └── app.js
│
├── terraform/
│   ├── persistent/                   # S3 + CloudFront (no se destruye)
│   └── app/                          # Lambda + API Gateway + IAM
│
├── scripts/
│   ├── deploy_lambda.sh              # Build + deploy del código Lambda
│   └── deploy_frontend.sh            # Sync frontend a S3 + invalidar cache
│
├── prompts/                          # Prompts para Amazon Bedrock
│   ├── documentation_prompt.txt
│   └── suggestions_prompt.txt
│
└── requirements.txt                  # Dependencias Python (ejecución local)


Copy

Insert at cursor
Servicios AWS Analizados
Categoría	Servicios
Networking	VPCs, Subnets, Internet Gateways, NAT Gateways, Route Tables, VPC Peering, Elastic IPs
Compute	EC2 Instances
Database	RDS Instances
Containers	ECS Clusters (con Services), EKS Clusters
Storage	EFS File Systems
Load Balancing	ALB, NLB (con Listeners y Target Groups)
Connectivity	Transit Gateways, VPN (Gateways, Customer Gateways, Connections), Direct Connect
Security	Security Groups
Seguridad
Sin credenciales estáticas: la Lambda usa AssumeRole con credenciales temporales (1 hora)

Nunca se escriben Access Keys: el flujo es exclusivamente AssumeRole

Outputs encriptados: S3 con SSE-S3 (AES256)

Lifecycle automático: outputs se eliminan a los 30 días

Bucket privado: acceso solo vía presigned URLs generadas por Lambda

Sin autenticación web (por ahora): pendiente Cognito para futuro

Requisitos para el Cliente
El cliente debe crear un rol IAM en su cuenta:

Nombre: infra-explorer-read-only

Política: ReadOnlyAccess (AWS managed policy)

Trust Policy:

{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Principal": {
                "AWS": "arn:aws:iam::590183851235:role/infra-explorer-lambda-role"
            },
            "Action": "sts:AssumeRole"
        }
    ]
}

Copy

Insert at cursor
json
Ejecución Local (legacy)
El proyecto también puede ejecutarse localmente con FastAPI:

source venv/bin/activate
aws-vault exec infra-explorer -- uvicorn src.web.app:app --reload --port 8000

Copy

Insert at cursor
bash
Roadmap
Fase	Descripción	Estado
1	Extracción de infraestructura con boto3	✅
2	Integración con Amazon Bedrock (Claude Sonnet 4)	✅
3	Validación y configuración (error handling, argparse)	✅
4	Servicios expandidos (RT, ELB, TGW, VPN, EIP, DX, ECS, EFS, EKS)	✅
5	Optimización de prompts	✅
6	Diagramas draw.io (generación programática con XML)	✅
7	Refactor: sesión boto3 inyectable + paginación	✅
8	Interfaz web (FastAPI + Jinja2)	✅
9	Despliegue serverless (Terraform + Lambda + CloudFront)	✅
10	Autenticación (Amazon Cognito)	⬜ Pendiente
11	Historial de análisis + gestión de clientes	⬜ Pendiente
12	Pestañas en diagrama draw.io (por categoría)	⬜ Pendiente
13	Dominio personalizado (Route 53 + ACM)	⬜ Pendiente

---