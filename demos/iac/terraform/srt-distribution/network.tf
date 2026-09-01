## VPC

resource "huaweicloud_vpc" "main" {
  name = "${local.prefix}-vpc"
  cidr = var.vpc_cidr
}

resource "huaweicloud_vpc_subnet" "main" {
  name       = "${local.prefix}-subnet"
  vpc_id     = huaweicloud_vpc.main.id
  cidr       = var.vpc_cidr
  gateway_ip = cidrhost(var.vpc_cidr, 1)
}

## Security group

resource "huaweicloud_networking_secgroup" "main" {
  name        = "${local.prefix}-secgroup"
  description = "SRT distribution PoC security group"
}

# SSH
resource "huaweicloud_networking_secgroup_rule" "ssh" {
  direction         = "ingress"
  ethertype         = "IPv4"
  protocol          = "tcp"
  port_range_min    = 22
  port_range_max    = 22
  remote_ip_prefix  = var.ssh_source_cidr
  security_group_id = huaweicloud_networking_secgroup.main.id
}

# SRT (UDP 8890) within VPC
resource "huaweicloud_networking_secgroup_rule" "srt" {
  direction         = "ingress"
  ethertype         = "IPv4"
  protocol          = "udp"
  port_range_min    = 8890
  port_range_max    = 8890
  remote_ip_prefix  = var.vpc_cidr
  security_group_id = huaweicloud_networking_secgroup.main.id
}

# Dashboard HTTP (80) from anywhere
resource "huaweicloud_networking_secgroup_rule" "http" {
  direction         = "ingress"
  ethertype         = "IPv4"
  protocol          = "tcp"
  port_range_min    = 80
  port_range_max    = 80
  remote_ip_prefix  = "0.0.0.0/0"
  security_group_id = huaweicloud_networking_secgroup.main.id
}

# Egress all
resource "huaweicloud_networking_secgroup_rule" "egress" {
  direction         = "egress"
  ethertype         = "IPv4"
  protocol          = "any"
  remote_ip_prefix  = "0.0.0.0/0"
  security_group_id = huaweicloud_networking_secgroup.main.id
}

## Key pair

resource "huaweicloud_compute_keypair" "main" {
  name       = "${local.prefix}-key"
  public_key = var.ssh_public_key
}
