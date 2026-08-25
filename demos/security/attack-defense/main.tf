terraform {
  required_version = ">= 1.5.0"

  required_providers {
    huaweicloud = {
      source  = "huaweicloud/huaweicloud"
      version = ">= 1.36.0"
    }
  }
}

provider "huaweicloud" {
  region     = var.region
  access_key = var.access_key
  secret_key = var.secret_key
}

# ---------------------------------------------------------------------------
# Data source: Ubuntu 24.04 public image (replaces hardcoded UUIDs)
# ---------------------------------------------------------------------------

data "huaweicloud_images_images" "ubuntu" {
  name_regex   = var.image_name_regex
  architecture = "x86"
  visibility   = "public"
  os           = "Ubuntu"
}

locals {
  image_id = coalesce(var.image_id_override, data.huaweicloud_images_images.ubuntu.images[0].id)
}

# ---------------------------------------------------------------------------
# Network: 2 VPCs + subnets + security groups
# ---------------------------------------------------------------------------

module "vpc" {
  source = "./vpc"
}

# ---------------------------------------------------------------------------
# ECS: host (DVWA + HSS + CES) + attacker (sqlmap + brute-force)
# ---------------------------------------------------------------------------

module "ecs" {
  source = "./ecs"

  availability_zone         = var.availability_zone
  image_id                  = local.image_id
  ecs_password              = var.ecs_password
  host_flavor               = var.host_flavor
  attacker_flavor           = var.attacker_flavor
  system_disk_type          = var.system_disk_type
  host_system_disk_size     = var.host_system_disk_size
  attacker_system_disk_size = var.attacker_system_disk_size
  eip_bandwidth             = var.eip_bandwidth
  host_sg_id                = module.vpc.host_sg_id
  attacker_sg_id            = module.vpc.attacker_sg_id
  host_subnet_id            = module.vpc.host_subnet_id
  attacker_subnet_id        = module.vpc.attacker_subnet_id
}

# ---------------------------------------------------------------------------
# CFW (Cloud Firewall) — optional, defense-in-depth at the perimeter
# ---------------------------------------------------------------------------

module "cfw" {
  count  = var.enable_cfw ? 1 : 0
  source = "./cfw"

  host_eip_id      = module.ecs.host_eip_id
  host_eip_address = module.ecs.host_eip
  attacker_eip     = module.ecs.attacker_eip
}

# ---------------------------------------------------------------------------
# WAF (Web Application Firewall) — optional, L7 protection
# ---------------------------------------------------------------------------

module "waf" {
  count  = var.enable_waf ? 1 : 0
  source = "./waf"

  host_eip    = module.ecs.host_eip
  domain_name = var.domain_name
}

# ---------------------------------------------------------------------------
# DNS — CNAME to WAF (only when WAF is enabled)
# ---------------------------------------------------------------------------

module "dns" {
  count  = var.enable_waf ? 1 : 0
  source = "./dns"

  waf_access_code = module.waf[0].access_code
  dns_zone_name   = var.public_zone
  domain_name     = var.domain_name
}
