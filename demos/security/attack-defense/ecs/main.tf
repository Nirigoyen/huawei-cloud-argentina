terraform {
  required_providers {
    huaweicloud = {
      source = "huaweicloud/huaweicloud"
    }
  }
}

# Host ECS: DVWA + HSS + CES
resource "huaweicloud_compute_instance" "host" {
  name               = "securityDemo-host"
  image_id           = var.image_id
  flavor_id          = var.host_flavor
  availability_zone  = var.availability_zone
  admin_pass         = var.ecs_password
  security_group_ids = [var.host_sg_id]
  agent_list         = "ces,hss"
  system_disk_type   = var.system_disk_type
  system_disk_size   = var.host_system_disk_size
  user_data = base64encode(templatefile("${path.module}/../cloud-init/host.yaml.tpl", {
    ecs_password = var.ecs_password
  }))

  network {
    uuid = var.host_subnet_id
  }

  tags = {
    Name    = "securityDemo-host"
    Project = "attack-defense"
  }
}

# Attacker ECS: sqlmap + SSH brute-force
resource "huaweicloud_compute_instance" "attacker" {
  name               = "securityDemo-attacker"
  image_id           = var.image_id
  flavor_id          = var.attacker_flavor
  availability_zone  = var.availability_zone
  admin_pass         = var.ecs_password
  security_group_ids = [var.attacker_sg_id]
  system_disk_type   = var.system_disk_type
  system_disk_size   = var.attacker_system_disk_size

  user_data = base64encode(templatefile("${path.module}/../cloud-init/attacker.yaml.tpl", {
    host_ip      = huaweicloud_vpc_eip.host_eip.address
    ecs_password = var.ecs_password
    bruteforce_b64 = base64encode(
      replace(file("${path.module}/../scripts/ssh_bruteforce.py"), "__HOST_IP__", huaweicloud_vpc_eip.host_eip.address)
    )
  }))

  network {
    uuid = var.attacker_subnet_id
  }

  tags = {
    Name    = "securityDemo-attacker"
    Project = "attack-defense"
  }
}

# EIPs
resource "huaweicloud_vpc_eip" "host_eip" {
  publicip {
    type = "5_bgp"
  }
  bandwidth {
    name        = "securityDemo-host-eip"
    size        = var.eip_bandwidth
    share_type  = "PER"
    charge_mode = "traffic"
  }
}

resource "huaweicloud_vpc_eip" "attacker_eip" {
  publicip {
    type = "5_bgp"
  }
  bandwidth {
    name        = "securityDemo-attacker-eip"
    size        = var.eip_bandwidth
    share_type  = "PER"
    charge_mode = "traffic"
  }
}

resource "huaweicloud_compute_eip_associate" "host" {
  instance_id = huaweicloud_compute_instance.host.id
  public_ip   = huaweicloud_vpc_eip.host_eip.address
}

resource "huaweicloud_compute_eip_associate" "attacker" {
  instance_id = huaweicloud_compute_instance.attacker.id
  public_ip   = huaweicloud_vpc_eip.attacker_eip.address
}
