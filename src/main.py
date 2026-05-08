import argparse
from core.session_manager import SessionManager
from core.orchestrator import InfraOrchestrator

ROLE_NAME = "cct_role_read_only"


def main():
    parser = argparse.ArgumentParser(description="AWS Infra Explorer AI")
    parser.add_argument("--region", default="eu-west-1", help="AWS region to analyze (default: eu-west-1)")
    parser.add_argument("--account-id", help="AWS Account ID for AssumeRole (uses cct_role_read_only)")
    args = parser.parse_args()

    try:
        role_arn = f"arn:aws:iam::{args.account_id}:role/{ROLE_NAME}" if args.account_id else None
        session = SessionManager(region_name=args.region, role_arn=role_arn)
        orchestrator = InfraOrchestrator(session=session)
        results = orchestrator.run()

        print(f"\nProceso completado. Archivos generados:")
        for name, path in results.items():
            print(f"  - {name}: {path}")
        print()

    except KeyboardInterrupt:
        print("\n\nProceso cancelado por el usuario.")
    except Exception as e:
        print(f"\nError inesperado: {e}\n")


if __name__ == "__main__":
    main()
