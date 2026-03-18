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
├── src                              # Main source code of the application
│   │
│   ├── extractors                   # Modules responsible for extracting infrastructure data from AWS using boto3
│   │   ├── __init__.py
│   │   ├── vpc_extractor.py         # Extracts VPCs and Subnets
│   │   ├── igw_extractor.py         # Extracts Internet Gateways
│   │   ├── natgw_extractor.py       # Extracts NAT Gateways
│   │   ├── sg_extractor.py          # Extracts Security Groups
│   │   ├── ec2_extractor.py         # Extracts EC2 Instances
│   │   └── rds_extractor.py         # Extracts RDS Instances
│   │
│   ├── models                       # Data models representing AWS infrastructure in a clean and structured format
│   │   ├── __init__.py
│   │   └── infra_model.py           # Core infrastructure data model used across the project
│   │
│   ├── core                         # Core orchestration logic that coordinates extractors and builds the final model
│   │   ├── __init__.py
│   │   └── orchestrator.py          # Orchestrator that runs all extractors and exports results
│   │
│   └── main.py                      # Application entry point (CLI execution starts here)
│
├── prompts                          # Prompt templates used when interacting with LLMs (Amazon Bedrock)
│
├── outputs                          # Generated outputs such as infrastructure JSON, reports, and diagrams
│
├── docs                             # Technical documentation, architecture decisions, and design notes
│
├── requirements.txt                 # Python dependencies required to run the project
│
└── README.md                        # Project overview and documentation