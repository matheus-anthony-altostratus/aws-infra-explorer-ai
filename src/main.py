from core.orchestrator import InfraOrchestrator


def main():

    region = "eu-west-1"

    orchestrator = InfraOrchestrator(region_name=region)
    infra = orchestrator.collect()
    output_path = orchestrator.export_to_json(infra)

    print(f"\nInfraestructura leída con éxito para la región {infra.region}.")
    print(f"Consulta los detalles en: {output_path}\n")


if __name__ == "__main__":
    main()
