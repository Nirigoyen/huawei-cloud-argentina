output "relay_public_ip" {
  description = "Public IP of the relay node."
  value       = huaweicloud_vpc_eip.relay.address
}

output "dashboard_url" {
  description = "URL of the SRT distribution dashboard."
  value       = "http://${huaweicloud_vpc_eip.relay.address}"
}

output "relay_private_ip" {
  description = "Private IP of the relay node."
  value       = huaweicloud_compute_instance.relay.access_ip_v4
}

output "emitter_private_ip" {
  description = "Private IP of the emitter node."
  value       = huaweicloud_compute_instance.emitter.access_ip_v4
}

output "receiver_private_ip" {
  description = "Private IP of the receiver node."
  value       = huaweicloud_compute_instance.receiver.access_ip_v4
}

output "srt_url" {
  description = "SRT listener URL on the relay (for external publishers/consumers)."
  value       = "srt://${huaweicloud_vpc_eip.relay.address}:8890"
}
