from extractors.vpc_extractor import VPCExtractor


def main():

    region = "eu-west-1"

    extractor = VPCExtractor(region_name=region)

    vpcs = extractor.extract_vpcs()

    print("\n=== AWS VPC Infrastructure ===\n")

    for vpc in vpcs:

        print(f"VPC: {vpc.resource_id}")
        print(f"CIDR: {vpc.cidr_block}")

        if vpc.subnets:
            print("Subnets:")

            for subnet in vpc.subnets:
                print(f"  - {subnet.resource_id} ({subnet.cidr_block}) {subnet.availability_zone}")

        print()


if __name__ == "__main__":
    main()