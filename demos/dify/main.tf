terraform {
  required_version = ">= 1.5.0"

  required_providers {
    huaweicloud = {
      source  = "huaweicloud/huaweicloud"
      version = ">= 1.36.0"
    }
    random = {
      source  = "hashicorp/random"
      version = ">= 3.5.0"
    }
  }
}

provider "huaweicloud" {
  region     = var.region
  access_key = var.access_key
  secret_key = var.secret_key
}

# ---------------------------------------------------------------------------
# Data sources
# ---------------------------------------------------------------------------

data "huaweicloud_images_image" "ubuntu" {
  name_regex  = "^Ubuntu 22.04"
  os          = "Ubuntu"
  visibility  = "public"
  most_recent = true
}

# ---------------------------------------------------------------------------
# Keypair
# ---------------------------------------------------------------------------

resource "huaweicloud_kps_keypair" "dify" {
  name       = "dify-keypair"
  public_key = var.ssh_public_key
}

# ---------------------------------------------------------------------------
# Secrets (generated, not committed)
# ---------------------------------------------------------------------------

resource "random_password" "secret_key" {
  length  = 32
  special = false
}

resource "random_password" "plugin_key" {
  length  = 64
  special = false
}

# ---------------------------------------------------------------------------
# Network: VPC + subnet
# ---------------------------------------------------------------------------

resource "huaweicloud_vpc" "dify" {
  name = "dify-vpc"
  cidr = "10.0.0.0/16"
}

resource "huaweicloud_vpc_subnet" "dify" {
  name          = "dify-subnet"
  cidr          = "10.0.1.0/24"
  gateway_ip    = "10.0.1.1"
  vpc_id        = huaweicloud_vpc.dify.id
  primary_dns   = "100.125.1.250"
  secondary_dns = "100.125.21.250"
}

# ---------------------------------------------------------------------------
# Security group: Dify ECS (web 80/443 + SSH)
# ---------------------------------------------------------------------------

resource "huaweicloud_networking_secgroup" "dify" {
  name        = "dify-sg"
  description = "Dify ECS - web (80/443) + SSH"
}

resource "huaweicloud_networking_secgroup_rule" "dify_http" {
  direction         = "ingress"
  ethertype         = "IPv4"
  protocol          = "tcp"
  port_range_min    = 80
  port_range_max    = 80
  remote_ip_prefix  = "0.0.0.0/0"
  security_group_id = huaweicloud_networking_secgroup.dify.id
}

resource "huaweicloud_networking_secgroup_rule" "dify_https" {
  direction         = "ingress"
  ethertype         = "IPv4"
  protocol          = "tcp"
  port_range_min    = 443
  port_range_max    = 443
  remote_ip_prefix  = "0.0.0.0/0"
  security_group_id = huaweicloud_networking_secgroup.dify.id
}

resource "huaweicloud_networking_secgroup_rule" "dify_ssh" {
  direction         = "ingress"
  ethertype         = "IPv4"
  protocol          = "tcp"
  port_range_min    = 22
  port_range_max    = 22
  remote_ip_prefix  = "0.0.0.0/0"
  security_group_id = huaweicloud_networking_secgroup.dify.id
}

# ---------------------------------------------------------------------------
# Security group: Ollama ECS (embeddings API 11434 from VPC + SSH)
# ---------------------------------------------------------------------------

resource "huaweicloud_networking_secgroup" "ollama" {
  name        = "ollama-sg"
  description = "Ollama ECS - embeddings API (11434) from VPC + SSH"
}

resource "huaweicloud_networking_secgroup_rule" "ollama_api" {
  direction         = "ingress"
  ethertype         = "IPv4"
  protocol          = "tcp"
  port_range_min    = 11434
  port_range_max    = 11434
  remote_ip_prefix  = "10.0.0.0/16"
  security_group_id = huaweicloud_networking_secgroup.ollama.id
}

resource "huaweicloud_networking_secgroup_rule" "ollama_ssh" {
  direction         = "ingress"
  ethertype         = "IPv4"
  protocol          = "tcp"
  port_range_min    = 22
  port_range_max    = 22
  remote_ip_prefix  = "0.0.0.0/0"
  security_group_id = huaweicloud_networking_secgroup.ollama.id
}

# ---------------------------------------------------------------------------
# Security group: RDS PostgreSQL (5432 from VPC)
# ---------------------------------------------------------------------------

resource "huaweicloud_networking_secgroup" "rds" {
  name        = "rds-sg"
  description = "RDS PostgreSQL - 5432 from VPC"
}

resource "huaweicloud_networking_secgroup_rule" "rds_pg" {
  direction         = "ingress"
  ethertype         = "IPv4"
  protocol          = "tcp"
  port_range_min    = 5432
  port_range_max    = 5432
  remote_ip_prefix  = "10.0.0.0/16"
  security_group_id = huaweicloud_networking_secgroup.rds.id
}

# ---------------------------------------------------------------------------
# EIP for Dify
# ---------------------------------------------------------------------------

resource "huaweicloud_vpc_eip" "dify" {
  publicip {
    type       = "5_bgp"
    ip_version = 4
  }

  bandwidth {
    name        = "dify-eip-bandwidth"
    size        = var.eip_bandwidth
    share_type  = "PER"
    charge_mode = "traffic"
  }
}

# ---------------------------------------------------------------------------
# RDS PostgreSQL (metadata DB + pgvector vector store)
# ---------------------------------------------------------------------------

resource "huaweicloud_rds_instance" "dify" {
  name              = "dify-rds"
  flavor            = var.rds_flavor
  availability_zone = [var.availability_zone]

  db {
    type     = "PostgreSQL"
    version  = "15"
    password = var.rds_password
  }

  volume {
    type = "ULTRAHIGH"
    size = 100
  }

  vpc_id            = huaweicloud_vpc.dify.id
  subnet_id         = huaweicloud_vpc_subnet.dify.id
  security_group_id = huaweicloud_networking_secgroup.rds.id
}

# ---------------------------------------------------------------------------
# Ollama ECS (bge-m3 embeddings, private only — no EIP)
# ---------------------------------------------------------------------------

resource "huaweicloud_compute_instance" "ollama" {
  name               = "ollama-ecs"
  flavor_id          = var.ollama_flavor
  image_id           = data.huaweicloud_images_image.ubuntu.id
  availability_zone  = var.availability_zone
  key_pair           = huaweicloud_kps_keypair.dify.name
  security_group_ids = [huaweicloud_networking_secgroup.ollama.id]
  user_data          = base64encode(file("cloud-init/ollama-cloud-init.yaml"))

  network {
    uuid = huaweicloud_vpc_subnet.dify.id
  }

  tags = {
    Name    = "ollama-ecs"
    Project = "dify"
  }
}

# ---------------------------------------------------------------------------
# Dify ECS (web app, EIP associated after creation)
# ---------------------------------------------------------------------------

locals {
  dify_env = templatefile("templates/dify-env.tpl", {
    rds_host     = huaweicloud_rds_instance.dify.private_ips[0]
    rds_password = var.rds_password
    dify_eip     = huaweicloud_vpc_eip.dify.address
    secret_key   = random_password.secret_key.result
    plugin_key   = random_password.plugin_key.result
  })
}

resource "huaweicloud_compute_instance" "dify" {
  name               = "dify-ecs"
  flavor_id          = var.dify_flavor
  image_id           = data.huaweicloud_images_image.ubuntu.id
  availability_zone  = var.availability_zone
  key_pair           = huaweicloud_kps_keypair.dify.name
  security_group_ids = [huaweicloud_networking_secgroup.dify.id]

  user_data = base64encode(templatefile("templates/dify-cloud-init.yaml.tpl", {
    rds_host     = huaweicloud_rds_instance.dify.private_ips[0]
    rds_password = var.rds_password
    dify_eip     = huaweicloud_vpc_eip.dify.address
    dify_version = var.dify_version
    env_content  = local.dify_env
  }))

  network {
    uuid = huaweicloud_vpc_subnet.dify.id
  }

  tags = {
    Name    = "dify-ecs"
    Project = "dify"
  }
}

resource "huaweicloud_compute_eip_associate" "dify" {
  instance_id = huaweicloud_compute_instance.dify.id
  public_ip   = huaweicloud_vpc_eip.dify.address
}
