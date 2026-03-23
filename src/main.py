import argparse
from core.orchestrator import InfraOrchestrator


def main():

    parser = argparse.ArgumentParser(description="AWS Infra Explorer AI")
    parser.add_argument("--region", default="eu-west-1", help="AWS region to analyze (default: eu-west-1)")
    args = parser.parse_args()

    try:
        orchestrator = InfraOrchestrator(region_name=args.region)
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
