# aws-infra-explorer-ai
AWS Infra Explorer AI is an internal tool designed to automatically analyze AWS infrastructure and generate clear technical documentation.

The tool connects to an AWS account using read-only permissions and extracts infrastructure data such as VPCs, EC2 instances, databases, and networking components.

Using AI models through Amazon Bedrock, it generates:

- Architecture diagrams
- Technical documentation
- Infrastructure explanations
- Improvement suggestions based on AWS best practices

## Project Goals

- Reduce time required to understand client infrastructures
- Improve onboarding for new engineers
- Standardize infrastructure documentation
- Provide automated architecture insights

## Status

Project currently under development (MVP phase).

aws-infra-explorer-ai
│
├── src
│   │
│   ├── extractors
│   │   ├── __init__.py
│   │
│   ├── models
│   │   ├── __init__.py
│   │
│   ├── core
│   │   ├── __init__.py
│   │
│   └── main.py
│
├── prompts
│
├── outputs
│
├── docs
│
├── requirements.txt
│
└── README.md