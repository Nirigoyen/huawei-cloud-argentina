output "host_eip" {
  value = huaweicloud_vpc_eip.host_eip.address
}

output "host_eip_id" {
  value = huaweicloud_vpc_eip.host_eip.id
}

output "attacker_eip" {
  value = huaweicloud_vpc_eip.attacker_eip.address
}
