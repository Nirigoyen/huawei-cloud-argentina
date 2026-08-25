output "host_vpc_id" {
  value = huaweicloud_vpc.host.id
}

output "attacker_vpc_id" {
  value = huaweicloud_vpc.attacker.id
}

output "host_subnet_id" {
  value = huaweicloud_vpc_subnet.host.id
}

output "attacker_subnet_id" {
  value = huaweicloud_vpc_subnet.attacker.id
}

output "host_sg_id" {
  value = huaweicloud_networking_secgroup.host.id
}

output "attacker_sg_id" {
  value = huaweicloud_networking_secgroup.attacker.id
}
