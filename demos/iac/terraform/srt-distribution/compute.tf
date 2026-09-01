## Image lookup

data "huaweicloud_images_image" "ubuntu" {
  name_regex  = var.image_name
  most_recent = true
}

## Relay (with EIP + dashboard)

resource "huaweicloud_compute_instance" "relay" {
  name              = "${local.prefix}-relay"
  image_id          = data.huaweicloud_images_image.ubuntu.id
  flavor_id         = var.ecs_flavor_id
  availability_zone = var.availability_zone
  admin_pass        = var.ecs_password
  key_pair          = huaweicloud_compute_keypair.main.name

  network {
    uuid = huaweicloud_vpc_subnet.main.id
  }

  security_group_ids = [huaweicloud_networking_secgroup.main.id]

  user_data = templatefile("${path.module}/scripts/relay-init.sh.tpl", {
    project_name   = var.project_name
    dashboard_title = var.dashboard_title
    index_html     = local.index_html
  })

  tags = {
    Role = "relay"
    Project = local.prefix
  }
}

resource "huaweicloud_vpc_eip" "relay" {
  publicip {
    type = "5_bgp"
  }
  bandwidth {
    name = "${local.prefix}-relay-eip"
    size = 5
  }
}

resource "huaweicloud_compute_eip_associate" "relay" {
  instance_id = huaweicloud_compute_instance.relay.id
  public_ip   = huaweicloud_vpc_eip.relay.address
}

## Emitter

resource "huaweicloud_compute_instance" "emitter" {
  name              = "${local.prefix}-emitter"
  image_id          = data.huaweicloud_images_image.ubuntu.id
  flavor_id         = var.ecs_flavor_id
  availability_zone = var.availability_zone
  admin_pass        = var.ecs_password
  key_pair          = huaweicloud_compute_keypair.main.name

  network {
    uuid = huaweicloud_vpc_subnet.main.id
  }

  security_group_ids = [huaweicloud_networking_secgroup.main.id]

  user_data = templatefile("${path.module}/scripts/emitter-init.sh.tpl", {
    project_name  = var.project_name
    relay_ip      = huaweicloud_compute_instance.relay.access_ip_v4
    srt_latency_us = var.srt_latency_us
  })

  tags = {
    Role = "emitter"
    Project = local.prefix
  }
}

## Receiver

resource "huaweicloud_compute_instance" "receiver" {
  name              = "${local.prefix}-receiver"
  image_id          = data.huaweicloud_images_image.ubuntu.id
  flavor_id         = var.ecs_flavor_id
  availability_zone = var.availability_zone
  admin_pass        = var.ecs_password
  key_pair          = huaweicloud_compute_keypair.main.name

  network {
    uuid = huaweicloud_vpc_subnet.main.id
  }

  security_group_ids = [huaweicloud_networking_secgroup.main.id]

  user_data = templatefile("${path.module}/scripts/receiver-init.sh.tpl", {
    project_name   = var.project_name
    relay_ip       = huaweicloud_compute_instance.relay.access_ip_v4
    consumer_count  = var.consumer_count
    srt_latency_us = var.srt_latency_us
  })

  tags = {
    Role = "receiver"
    Project = local.prefix
  }
}
