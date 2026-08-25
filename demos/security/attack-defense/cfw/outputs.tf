output "firewall_id" {
  value = huaweicloud_cfw_firewall.demo.id
}

output "object_id" {
  value = huaweicloud_cfw_firewall.demo.protect_objects[0].object_id
}
