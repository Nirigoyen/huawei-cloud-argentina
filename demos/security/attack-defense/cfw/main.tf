terraform {
  required_providers {
    huaweicloud = {
      source = "huaweicloud/huaweicloud"
    }
  }
}

resource "huaweicloud_cfw_firewall" "demo" {
  name = "securityDemo-cfw"

  flavor {
    version = "Professional"
  }

  # Enable IPS at the firewall level (1=enabled, 0=disabled)
  ips_switch_status = 1
  # Medium protection mode (0=observe, 1=strict, 2=medium, 3=loose)
  ips_protection_mode = 2
}

# Protect the host EIP with CFW
resource "huaweicloud_cfw_eip_protection" "host" {
  object_id = huaweicloud_cfw_firewall.demo.protect_objects[0].object_id

  protected_eip {
    id          = var.host_eip_id
    public_ipv4 = var.host_eip_address
  }
}

# Set IPS rules to ENABLE (block mode, not just observe)
resource "huaweicloud_cfw_ips_rule_mode_change" "enable" {
  object_id = huaweicloud_cfw_firewall.demo.protect_objects[0].object_id
  status    = "ENABLE"
}

# ACL rule: allow attacker IP to reach the host (granular access control demo)
resource "huaweicloud_cfw_acl_rule" "allow_attacker" {
  name                = "allow-attacker-to-host"
  object_id           = huaweicloud_cfw_firewall.demo.protect_objects[0].object_id
  description         = "Allow attacker IP to reach the host (granular CFW control demo)"
  type                = 0 # Internet rule
  address_type        = 0 # IPv4
  action_type         = 0 # allow
  long_connect_enable = 0
  status              = 1 # enabled
  direction           = 0 # inbound

  source_addresses      = [var.attacker_eip]
  destination_addresses = [var.host_eip_address]

  custom_services {
    protocol    = 6 # TCP
    source_port = "0"
    dest_port   = "0"
  }

  sequence {
    top = 1
  }
}
