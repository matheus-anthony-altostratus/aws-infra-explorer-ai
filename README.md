# aws-infra-explorer-ai

AWS Infra Explorer AI is an internal tool designed to automatically analyze AWS infrastructure and generate clear technical documentation.

The tool connects to an AWS account using read-only permissions and extracts infrastructure data such as VPCs, EC2 instances, databases, and networking components.

Using AI models through Amazon Bedrock (Claude Sonnet 4), it generates:

- Technical documentation in Markdown
- Architecture diagrams in Mermaid format
- Improvement suggestions based on AWS Well-Architected Framework

## Project Goals

- Reduce time required to understand client infrastructures
- Improve onboarding for new engineers
- Standardize infrastructure documentation
- Provide automated architecture insights

## Status

MVP functional — Fase 1 (extraction) and Fase 2 (Bedrock integration) completed.

## Prerequisites

- Python 3.12+
- AWS account with ReadOnlyAccess
- IAM policy with `bedrock:InvokeModel` permission
- [aws-vault](https://github.com/99designs/aws-vault) configured with the target account profile

## Setup

```bash
# Clone the repository
git clone <repository-url>
cd aws-infra-explorer-ai

# Create and activate virtual environment
python3.12 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt


Usage 
--------------------------------------------------------------------------------------
python3 src/main.py

Example output:

Extrayendo infraestructura de la región eu-west-1...
Generando reportes con Amazon Bedrock...
Generando documentación técnica...
Generando diagrama Mermaid...
Generando sugerencias de mejora...

Proceso completado. Archivos generados:
  - infra_json: outputs/infra_eu-west-1.json
  - documentation: outputs/documentation_eu-west-1.md
  - diagram: outputs/diagram_eu-west-1.md
  - suggestions: outputs/suggestions_eu-west-1.md
----------------------------------------------------------------------------------------


Generated Outputs
----------------------------------------------------------------------------------------
File	Description

infra_<region>.json	Structured inventory of all extracted resources
documentation_<region>.md	Technical narrative describing the infrastructure
diagram_<region>.md	Mermaid diagram of the architecture
suggestions_<region>.md	Improvement suggestions based on Well-Architected Framework
----------------------------------------------------------------------------------------


AWS Permissions Required
----------------------------------------------------------------------------------------
The IAM user/role needs:

ReadOnlyAccess (AWS managed policy) — for infrastructure extraction

Custom policy with bedrock:InvokeModel — for AI report generation
----------------------------------------------------------------------------------------

Project Structure
----------------------------------------------------------------------------------------

aws-infra-explorer-ai
│
├── src                              # Main source code
│   ├── extractors                   # AWS infrastructure data extractors (boto3)
│   │   ├── __init__.py
│   │   ├── vpc_extractor.py         # Extracts VPCs and Subnets
│   │   ├── igw_extractor.py         # Extracts Internet Gateways
│   │   ├── natgw_extractor.py       # Extracts NAT Gateways
│   │   ├── sg_extractor.py          # Extracts Security Groups
│   │   ├── ec2_extractor.py         # Extracts EC2 Instances
│   │   └── rds_extractor.py         # Extracts RDS Instances
│   │
│   ├── generators                   # AI report generation using Amazon Bedrock
│   │   ├── __init__.py
│   │   └── bedrock_generator.py     # Bedrock client + report generation logic
│   │
│   ├── models                       # Data models for AWS infrastructure
│   │   ├── __init__.py
│   │   └── infra_model.py           # Core data models used across the project
│   │
│   ├── core                         # Orchestration logic
│   │   ├── __init__.py
│   │   └── orchestrator.py          # Coordinates extractors, generators, and exports
│   │
│   └── main.py                      # Application entry point
│
├── prompts                          # Prompt templates for Amazon Bedrock
│   ├── documentation_prompt.txt     # Prompt for technical documentation
│   ├── diagram_prompt.txt           # Prompt for Mermaid diagram
│   └── suggestions_prompt.txt       # Prompt for improvement suggestions
│
├── outputs                          # Generated outputs (gitignored)
│
├── docs                             # Technical documentation and design notes
│
├── requirements.txt                 # Python dependencies
│
└── README.md                        # Project documentation
