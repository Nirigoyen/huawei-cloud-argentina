terraform {
  required_providers {
    huaweicloud = {
      source = "huaweicloud/huaweicloud"
    }
  }
}

resource "huaweicloud_vpc" "host" {
  name = "securityDemo-host"
  cidr = "10.0.0.0/16"
}

resource "huaweicloud_vpc" "attacker" {
  name = "securityDemo-attacker"
  cidr = "10.1.0.0/16"
}

resource "huaweicloud_vpc_subnet" "host" {
  vpc_id     = huaweicloud_vpc.host.id
  name       = "securityDemo-host-subnet"
  cidr       = "10.0.1.0/24"
  gateway_ip = "10.0.1.1"
}

resource "huaweicloud_vpc_subnet" "attacker" {
  vpc_id     = huaweicloud_vpc.attacker.id
  name       = "securityDemo-attacker-subnet"
  cidr       = "10.1.1.0/24"
  gateway_ip = "10.1.1.1"
}

# Security group: host — SSH (22) + HTTP (80) from anywhere
# ponytail: huaweicloud_networking_secgroup is region-scoped (not VPC-scoped);
# huaweicloud_vpc_secgroup does not exist in the provider.
resource "huaweicloud_networking_secgroup" "host" {
  name        = "securityDemo-host-sg"
  description = "Host ECS — SSH + HTTP"
}

resource "huaweicloud_networking_secgroup_rule" "host_ssh" {
  security_group_id = huaweicloud_networking_secgroup.host.id
  direction         = "ingress"
  ethertype         = "IPv4"
  protocol          = "tcp"
  port_range_min    = 22
  port_range_max    = 22
  remote_ip_prefix  = "0.0.0.0/0"
}

resource "huaweicloud_networking_secgroup_rule" "host_http" {
  security_group_id = huaweicloud_networking_secgroup.host.id
  direction         = "ingress"
  ethertype         = "IPv4"
  protocol          = "tcp"
  port_range_min    = 80
  port_range_max    = 80
  remote_ip_prefix  = "0.0.0.0/0"
}

# Security group: attacker — SSH (22) from anywhere
resource "huaweicloud_networking_secgroup" "attacker" {
  name        = "securityDemo-attacker-sg"
  description = "Attacker ECS — SSH only"
}

resource "huaweicloud_networking_secgroup_rule" "attacker_ssh" {
  security_group_id = huaweicloud_networking_secgroup.attacker.id
  direction         = "ingress"
  ethertype         = "IPv4"
  protocol          = "tcp"
  port_range_min    = 22
  port_range_max    = 22
  remote_ip_prefix  = "0.0.0.0/0"
}
