import os

import pytest


def test_main_tf_exists():
    assert os.path.exists("modules/vpc/main.tf"), "modules/vpc/main.tf not found"


def test_variables_tf_exists():
    assert os.path.exists("modules/vpc/variables.tf"), "modules/vpc/variables.tf not found"


def test_outputs_tf_exists():
    assert os.path.exists("modules/vpc/outputs.tf"), "modules/vpc/outputs.tf not found"


def test_main_tf_has_vpc():
    with open("modules/vpc/main.tf") as f:
        content = f.read()
    assert "aws_vpc" in content, "Must define aws_vpc"
    assert "enable_dns_support" in content, "Must enable DNS support"
    assert "enable_dns_hostnames" in content, "Must enable DNS hostnames"


def test_main_tf_has_subnets():
    with open("modules/vpc/main.tf") as f:
        content = f.read()
    assert "aws_subnet" in content, "Must define subnets"
    # Should have at least 4 subnet definitions (2 public + 2 private)
    import re
    subnet_count = len(re.findall(r"aws_subnet\b", content))
    assert subnet_count >= 4, f"Expected 4+ subnets, found {subnet_count}"


def test_main_tf_has_gateways():
    with open("modules/vpc/main.tf") as f:
        content = f.read()
    assert "aws_internet_gateway" in content, "Must have Internet Gateway"
    assert "aws_nat_gateway" in content, "Must have NAT Gateway"


def test_main_tf_has_route_tables():
    with open("modules/vpc/main.tf") as f:
        content = f.read()
    assert "aws_route_table" in content, "Must have route tables"
    assert "aws_route_table_association" in content, "Must have route table associations"
    assert "0.0.0.0/0" in content, "Must route 0.0.0.0/0"


def test_variables_defined():
    with open("modules/vpc/variables.tf") as f:
        content = f.read()
    for var in ["cidr_block", "environment", "project_name", "region",
                "public_subnet_cidrs", "private_subnet_cidrs"]:
        assert f'variable "{var}"' in content or f"variable \"{var}\"" in content, \
            f"Missing variable: {var}"


def test_outputs_defined():
    with open("modules/vpc/outputs.tf") as f:
        content = f.read()
    for out in ["vpc_id", "public_subnet_ids", "private_subnet_ids",
                "nat_gateway_id", "internet_gateway_id"]:
        assert f'output "{out}"' in content or f"output \"{out}\"" in content, \
            f"Missing output: {out}"


def test_has_tags():
    with open("modules/vpc/main.tf") as f:
        content = f.read()
    assert "tags" in content, "Must use tags"
    assert "Environment" in content or "environment" in content, "Must tag Environment"
    assert "Project" in content or "project" in content, "Must tag Project"
