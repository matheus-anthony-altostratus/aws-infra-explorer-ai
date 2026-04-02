# aws-infra-explorer-ai

AWS Infra Explorer AI is an internal tool designed to automatically analyze AWS infrastructure and generate clear technical documentation and architecture diagrams.

The tool connects to an AWS account using read-only permissions and extracts infrastructure data such as VPCs, EC2 instances, databases, networking, containers, and storage components.

It generates:

- Technical documentation in Markdown (powered by Amazon Bedrock - Claude Sonnet 4)
- Architecture diagrams in draw.io format (programmatically generated with AWS icons)
- Improvement suggestions based on AWS Well-Architected Framework (powered by Amazon Bedrock)

## Project Goals

- Reduce time required to understand client infrastructures
- Improve onboarding for new engineers
- Standardize infrastructure documentation
- Provide automated architecture insights and diagrams

## Status

See [Project Phases](#project-phases) for detailed progress.

## Prerequisites

- Python 3.12+
- AWS account with ReadOnlyAccess
- IAM policy with `bedrock:InvokeModel` permission (or `AmazonBedrockLimitedAccess` managed policy)
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
# Default region (eu-west-1)
aws-vault exec <profile> -- python3 src/main.py

# Custom region
aws-vault exec <profile> -- python3 src/main.py --region us-east-1

Supported AWS Services

Category	Services
Networking	VPCs, Subnets, Internet Gateways, NAT Gateways, Route Tables, VPC Peering, Elastic IPs
Compute	EC2 Instances
Database	RDS Instances
Containers	ECS Clusters (with Services), EKS Clusters
Storage	EFS File Systems
Load Balancing	ALB, NLB (with Listeners and Target Groups)
Connectivity	Transit Gateways, VPN (Gateways, Customer Gateways, Connections), Direct Connect
Security	Security Groups
AWS Permissions Required
The IAM user/role needs:

ReadOnlyAccess (AWS managed policy) — for infrastructure extraction

AmazonBedrockLimitedAccess (AWS managed policy) — for AI report generation

## Project Structure

aws-infra-explorer-ai
│
├── src/                              # Main source code
│   ├── extractors/                   # AWS infrastructure data extractors (boto3)
│   │   ├── vpc_extractor.py          # VPCs and Subnets
│   │   ├── igw_extractor.py          # Internet Gateways
│   │   ├── natgw_extractor.py        # NAT Gateways
│   │   ├── sg_extractor.py           # Security Groups
│   │   ├── ec2_extractor.py          # EC2 Instances
│   │   ├── rds_extractor.py          # RDS Instances
│   │   ├── rt_extractor.py           # Route Tables
│   │   ├── elb_extractor.py          # Load Balancers, Listeners, Target Groups
│   │   ├── tgw_extractor.py          # Transit Gateways, Attachments, Route Tables
│   │   ├── vpn_extractor.py          # VPN Gateways, Customer Gateways, Connections
│   │   ├── eip_extractor.py          # Elastic IPs
│   │   ├── peering_extractor.py      # VPC Peering
│   │   ├── dx_extractor.py           # Direct Connect
│   │   ├── ecs_extractor.py          # ECS Clusters and Services
│   │   ├── efs_extractor.py          # EFS File Systems
│   │   └── eks_extractor.py          # EKS Clusters
│   │
│   ├── generators/                   # Report and diagram generation
│   │   ├── bedrock_generator.py      # Bedrock client + AI report generation
│   │   └── drawio_generator.py       # draw.io diagram generation (XML)
│   │
│   ├── models/                       # Data models
│   │   └── infra_model.py            # Dataclasses for all AWS resources
│   │
│   ├── core/                         # Orchestration
│   │   └── orchestrator.py           # Coordinates extractors, generators, and exports
│   │
│   └── main.py                       # Entry point (argparse for --region)
│
├── prompts/                          # Prompt templates for Amazon Bedrock
│   ├── documentation_prompt.txt      # Technical documentation prompt
│   └── suggestions_prompt.txt        # Well-Architected suggestions prompt
│
├── outputs/                          # Generated outputs (gitignored)
├── requirements.txt                  # Python dependencies
└── README.md                         # Project documentation

## Project Phases

| Nº|----Phase-------------------------------------------------------------------------------------|---Status-----|
| 1 |	Infrastructure extraction with boto3 (VPC, EC2, RDS, SG, IGW, NAT GW)	                       | ✅ Completed |
| 2 | Amazon Bedrock integration (documentation, diagrams, suggestions)	                           | ✅ Completed |
| 3 | Validation and configuration (error handling, argparse, README)	                             | ✅ Completed |
| 4 | Expanded services (Route Tables, ELB, TGW, VPN, EIPs, Peering, DX, ECS, EFS, EKS)	           | ✅ Completed |
| 5 | Prompt optimization (report quality and completeness)	                                       | ✅ Completed |
| 6 | draw.io diagram generation (programmatic XML with AWS icons)	                               | ✅ Completed |
| 7 | Streamlit web interface	                                                                     | ⬜ Pending   |
| 8 | Opciones Multicuenta                                                                         | ⬜ Pending   |
| 9 |                                                                        | ⬜ Pending   |
| 10|                                                                          | ⬜ Pending   |
