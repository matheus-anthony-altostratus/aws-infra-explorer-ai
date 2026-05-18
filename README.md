# AWS Infra Explorer AI

Herramienta interna de Altostratus que analiza automáticamente la infraestructura AWS de cuentas de clientes y genera documentación técnica, sugerencias Well-Architected y diagramas de arquitectura — en minutos, sin credenciales estáticas.

---

## Flujo desde el punto de vista del usuario

Este diagrama muestra los pasos que sigue un ingeniero de Altostratus al usar la herramienta, sin entrar en detalles técnicos.

```
  ┌─────────────────────────────────────────────────────────────────┐
  │                        INGENIERO                                │
  └─────────────────────────────────────────────────────────────────┘

        │
        │  1. Abre la URL de la herramienta en el navegador
        ▼
  ┌─────────────────────────────────────────────────────────────────┐
  │  Pantalla de acceso                                             │
  │                                                                 │
  │   ¿Primera vez?  ──►  Se registra con su correo @altostratus.es │
  │                        Verifica el código que llega al correo   │
  │                                                                 │
  │   ¿Ya tiene cuenta?  ──►  Inicia sesión con email y contraseña  │
  └─────────────────────────────────────────────────────────────────┘

        │
        │  2. Accede al panel principal
        ▼
  ┌─────────────────────────────────────────────────────────────────┐
  │  Panel de la herramienta                                        │
  │                                                                 │
  │   Secciones disponibles:                                        │
  │   · Inicio      — resumen de la herramienta                     │
  │   · Cuentas     — gestión de cuentas AWS de clientes            │
  │   · Analizador  — lanzar un nuevo análisis                      │
  │   · Historial   — ver análisis anteriores del equipo            │
  │   · Guía        — instrucciones para configurar la cuenta       │
  └─────────────────────────────────────────────────────────────────┘

        │
        │  3. (Opcional) Registra la cuenta del cliente
        ▼
  ┌─────────────────────────────────────────────────────────────────┐
  │  Sección Cuentas                                                │
  │                                                                 │
  │   Añade la cuenta AWS del cliente con:                          │
  │   · Nombre del cliente / grupo                                  │
  │   · Account ID (número de 12 dígitos)                           │
  │   · Región por defecto y color identificador                    │
  │                                                                 │
  │   Esto permite seleccionarla directamente en el analizador      │
  │   sin tener que escribir el Account ID cada vez.                │
  └─────────────────────────────────────────────────────────────────┘

        │
        │  4. Lanza el análisis
        ▼
  ┌─────────────────────────────────────────────────────────────────┐
  │  Sección Analizador                                             │
  │                                                                 │
  │   · Selecciona la cuenta del cliente                            │
  │   · Selecciona la región a analizar                             │
  │   · Pulsa "Analizar Infraestructura"                            │
  │                                                                 │
  │   La herramienta muestra el progreso en tiempo real:            │
  │   🔐 Conectando con la cuenta...                                │
  │   🔍 Extrayendo infraestructura...                              │
  │   📝 Generando documentación con IA...                          │
  │   🏗️  Generando diagrama de arquitectura...                     │
  │   ☁️  Subiendo archivos...                                      │
  └─────────────────────────────────────────────────────────────────┘

        │
        │  5. Descarga los resultados
        ▼
  ┌─────────────────────────────────────────────────────────────────┐
  │  Resultados del análisis                                        │
  │                                                                 │
  │   Se generan 4 archivos listos para descargar:                  │
  │                                                                 │
  │   📊  infra.json          Inventario completo de recursos       │
  │   📄  documentation.md    Documentación técnica generada con IA │
  │   💡  suggestions.md      Sugerencias Well-Architected          │
  │   🏗️  diagram.drawio      Diagrama editable en diagrams.net     │
  │                                                                 │
  │   Los archivos están disponibles para descarga durante 1 hora.  │
  │   El análisis queda registrado en el historial del equipo.      │
  └─────────────────────────────────────────────────────────────────┘
```

---

## Flujo técnico — servicios AWS

Este diagrama muestra cómo interactúan los servicios AWS internamente desde que el ingeniero abre la herramienta hasta que descarga los archivos.

```
  ┌────────────┐
  │  Ingeniero │
  │ (Browser)  │
  └─────┬──────┘
        │
        │  Abre la URL  (HTTPS)
        ▼
  ┌─────────────┐        bucket policy: solo permite acceso
  │ CloudFront  │ ──OAC──► desde este CloudFront específico
  │   (CDN)     │        ┌──────────────────┐
  └─────┬───────┘        │   S3 — Frontend  │
        │                │   index.html     │
        │                │   app.js         │
        │                │   nav.js         │
        │                └──────────────────┘
        │
        │  El browser carga la app y muestra la pantalla de login
        │
        ├─────────────────────────────────────────────────────────┐
        │  PRIMERA VEZ: registro                                  │
        │                                                         │
        │  Browser ──► Cognito  (crea usuario)                    │
        │              Cognito  (envía código de verificación)    │
        │  Browser ──► Cognito  (confirma código)                 │
        │                                                         │
        │  SIGUIENTES VECES: login                                │
        │                                                         │
        │  Browser ──► Cognito  (email + contraseña)              │
        │  Cognito ──► Browser  (devuelve JWT)                    │
        └─────────────────────────────────────────────────────────┘
        │
        │  Con el JWT almacenado, el ingeniero lanza el análisis
        │
        │  POST /analyze  { account_id, region }
        │  Authorization: Bearer <JWT>
        ▼
  ┌─────────────┐
  │ API Gateway │  valida el JWT contra Cognito antes de continuar
  │  HTTP API   │  si el token es inválido o expirado → 401
  └─────┬───────┘
        │
        ▼
  ┌─────────────┐
  │   Lambda    │  invocación síncrona
  │  (router)   │  · guarda status "processing" en S3
  │             │  · se auto-invoca de forma asíncrona
  │             │  · devuelve 202 { analysis_id } al browser
  └─────┬───────┘
        │
        │  auto-invocación asíncrona (el trabajo real empieza aquí)
        ▼
  ┌─────────────┐
  │   Lambda    │
  │ (análisis)  │
  └──────┬──────┘
         │
         │  Paso 1 — Extracción de infraestructura
         ▼
  ┌──────────────────┐
  │  Cuenta Cliente  │  STS AssumeRole → credenciales temporales (1h)
  │                  │  rol: infra-explorer-read-only (solo lectura)
  │  17 extractores  │  extrae: VPCs, EC2, RDS, ECS, EKS, ELB,
  │  boto3           │          TGW, VPN, DX, EFS, SG, EIP...
  └──────┬───────────┘
         │
         │  Paso 2 — Generación de documentación con IA
         ▼
  ┌──────────────────┐
  │  Amazon Bedrock  │  recibe el JSON de infraestructura extraída
  │  Claude Sonnet 4 │  genera documentación técnica + sugerencias
  └──────┬───────────┘  Well-Architected (5 pilares)
         │
         │  Paso 3 — Generación del diagrama
         │  DrawioGenerator crea el XML con iconos AWS oficiales
         │
         │  Paso 4 — Subida de archivos
         ▼
  ┌──────────────────┐
  │   S3 — Outputs   │  sube los 4 archivos generados
  │                  │  actualiza status.json → "completed"
  │  infra.json      │  genera presigned URLs (validez 1h)
  │  docs.md         │  lifecycle automático: se eliminan a los 30 días
  │  suggestions.md  │
  │  diagram.drawio  │
  │  status.json     │
  └──────┬───────────┘
         │
         │  Paso 5 — Registro en historial
         ▼
  ┌──────────────────┐
  │    DynamoDB      │
  │                  │
  │  · accounts      │  cuentas AWS de clientes registradas
  │  · history       │  registro del análisis: quién, cuándo, qué cuenta
  └──────────────────┘

        │
        │  Mientras tanto, el browser hace polling cada 5 segundos
        │
        │  GET /status/{analysis_id}
        ▼
  ┌─────────────┐
  │ API Gateway │──► Lambda ──► S3 (lee status.json)
  └─────┬───────┘
        │
        │  Cuando status = "completed"
        │  devuelve { status, presigned_urls, documentation, suggestions }
        ▼
  ┌────────────┐
  │  Ingeniero │  descarga los archivos directamente desde S3
  │ (Browser)  │  via presigned URLs — validez 1 hora
  └────────────┘
```

---

## Pasos del flujo técnico

| # | Paso | Descripción |
|---|---|---|
| 1 | **Carga del frontend** | CloudFront sirve los archivos estáticos desde S3 via OAC. El bucket S3 nunca queda expuesto públicamente — solo CloudFront puede acceder a él. |
| 2 | **Autenticación** | Cognito gestiona el registro (solo `@altostratus.es`) y el login. Emite un JWT que el browser almacena y envía en cada petición. |
| 3 | **Lanzar análisis** | El frontend envía `POST /analyze` con el JWT. API Gateway valida el token antes de invocar Lambda. |
| 4 | **Respuesta inmediata** | Lambda (síncrona) guarda `status: processing` en S3, se auto-invoca de forma asíncrona y devuelve `202 { analysis_id }` al browser en menos de 1 segundo. |
| 5 | **Análisis en background** | Lambda (asíncrona) asume el rol `infra-explorer-read-only` en la cuenta cliente via STS, extrae la infraestructura con 16 extractores boto3, genera documentación y sugerencias con Bedrock, genera el diagrama draw.io y sube los 4 archivos a S3. |
| 6 | **Polling** | El browser consulta `GET /status/{analysis_id}` cada 5 segundos hasta recibir `status: completed`. |
| 7 | **Descarga** | El browser recibe las presigned URLs y el ingeniero descarga los archivos directamente desde S3 (validez 1 hora). |

---

## Recursos AWS utilizados

| Recurso | Para qué se usa |
|---|---|
| **CloudFront** | CDN que sirve el frontend al navegador. Es el único punto de entrada público. Accede a S3 via OAC — el bucket nunca queda expuesto directamente. |
| **S3 — Frontend** | Almacena los archivos estáticos: `index.html`, `app.js`, `nav.js` y assets. Solo accesible via CloudFront OAC, nunca de forma pública directa. |
| **S3 — Outputs** | Almacena los archivos generados por cada análisis: `infra.json`, `documentation.md`, `suggestions.md`, `diagram.drawio` y `status.json`. Acceso exclusivo via presigned URLs con 1h de validez. Lifecycle automático de 30 días. |
| **API Gateway (HTTP API)** | Expone los endpoints REST del backend. Valida el JWT de Cognito en cada petición antes de invocar Lambda. Rutas: `POST /analyze`, `GET /status/{id}`, `GET /history`, `GET/POST/PUT/DELETE /accounts`. |
| **Lambda — analyzer** | Función principal. Actúa como router HTTP, orquesta el análisis asíncrono, llama a STS / Bedrock / S3 y gestiona el CRUD de cuentas e historial en DynamoDB. |
| **Lambda — cognito-presignup** | Trigger pre-signup de Cognito. Bloquea el registro de cualquier email que no sea `@altostratus.es`. |
| **Amazon Cognito** | Gestiona la autenticación de los ingenieros. Emite JWTs que API Gateway valida en cada petición. |
| **Amazon Bedrock (Claude Sonnet 4)** | Genera la documentación técnica y las sugerencias Well-Architected a partir del JSON de infraestructura extraído. |
| **DynamoDB — accounts** | Almacena las cuentas AWS de clientes registradas, agrupadas por cliente. Incluye nombre, alias, región por defecto y color identificador. Permite seleccionar la cuenta directamente en el analizador sin escribir el Account ID a mano. |
| **DynamoDB — history** | Registra cada análisis completado: quién lo ejecutó, cuándo, sobre qué cuenta y región. Permite el historial compartido entre todos los ingenieros del equipo. |
| **IAM — lambda-role** | Rol que asume la Lambda. Permisos para invocar Bedrock, leer/escribir en S3, leer/escribir en DynamoDB y asumir el rol `infra-explorer-read-only` en cuentas cliente via STS. |
| **STS AssumeRole** | Permite acceder a la cuenta cliente sin credenciales estáticas. La Lambda asume el rol `infra-explorer-read-only` con credenciales temporales de 1 hora. |

---

## Infraestructura (Terraform)

Dos stacks independientes para separar lo que cambia frecuentemente de lo que no:

| Stack | Contenido | Cuándo tocar |
|---|---|---|
| `terraform/persistent/` | S3 buckets + CloudFront | Rara vez — **NO destruir** |
| `terraform/` | Lambda + API Gateway + IAM + Cognito + DynamoDB | Frecuente — destroy/apply sin miedo |

> ⚠️ Al hacer destroy/apply del stack de app, API Gateway se recrea con nueva URL.
> Hay que actualizar `API_URL` en `frontend/app.js` y redesplegar el frontend.

---

## Recursos desplegados

| Recurso | Valor |
|---|---|
| CloudFront URL | `https://d2y8h0jbecvclg.cloudfront.net` |
| CloudFront Distribution ID | `E1MHNIQHI7VQ5F` |
| S3 Frontend | `infra-explorer-frontend-sandbox` |
| S3 Outputs | `infra-explorer-outputs-sandbox` |
| API Gateway | `https://gh41sneumj.execute-api.eu-west-1.amazonaws.com` |
| Lambda Analyzer | `infra-explorer-analyzer` |
| Lambda Cognito Trigger | `infra-explorer-cognito-presignup` |
| Cognito User Pool | `eu-west-1_DyJrMHx9N` |
| Cognito Client ID | `1hk5o7m7h2pkvbc5eh79tdgg8n` |
| DynamoDB — Accounts | `infra-explorer-accounts` |
| DynamoDB — History | `infra-explorer-history` |

---

## Estructura del proyecto

```
aws-infra-explorer-ai/
├── src/
│   ├── lambda_handler.py          # Entry point Lambda — router HTTP + flujo asíncrono
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
│   ├── app.js                     # Auth (Cognito) + analizador + polling + cuentas
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
│   ├── dynamodb.tf                # Tablas accounts e history
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

## Outputs generados por análisis

| Archivo | Contenido |
|---|---|
| `infra_{region}.json` | Inventario estructurado de todos los recursos encontrados en la cuenta. |
| `documentation_{region}.md` | Documentación técnica generada con IA: resumen ejecutivo, arquitectura de red, recursos, seguridad. |
| `suggestions_{region}.md` | Recomendaciones basadas en los 5 pilares del AWS Well-Architected Framework. |
| `diagram_{region}.drawio` | Diagrama de arquitectura con iconos AWS oficiales. Editable en app.diagrams.net. |

---

## Seguridad

- **Sin credenciales estáticas** — AssumeRole con credenciales temporales de 1 hora via STS
- **JWT validado en cada petición** — API Gateway verifica el token de Cognito antes de invocar Lambda
- **Acceso restringido al equipo** — Pre-signup trigger bloquea cualquier email que no sea `@altostratus.es`
- **S3 outputs privado** — Nunca expuesto públicamente, acceso solo via presigned URLs (1h)
- **S3 frontend protegido** — Solo accesible via CloudFront OAC, sin acceso público directo al bucket
- **Outputs encriptados** — SSE-S3 (AES256) en reposo, lifecycle automático de 30 días

---

## Requisitos para el cliente

Antes de analizar una cuenta, el cliente debe crear un rol IAM con los siguientes parámetros:

- **Nombre del rol:** `infra-explorer-read-only`
- **Política adjunta:** `ReadOnlyAccess` (AWS managed policy)
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

Una vez creado el rol, el cliente solo necesita compartir su **Account ID** (número de 12 dígitos).

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

# Lambda + API Gateway + IAM + Cognito + DynamoDB
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
| 10 | Historial de análisis compartido + gestión de cuentas (DynamoDB) | ✅ |
| 11 | Diagrama draw.io con 7 pestañas por categoría + extractor DynamoDB | ✅ |
| 12 | Tech Profile — ficha técnica por cliente | ⬜ Pendiente |
| 13 | Análisis multi-región — consolidar varias regiones en un único output | ⬜ Pendiente |
| 14 | Dominio personalizado (Route 53 + ACM) | ⬜ Pendiente |