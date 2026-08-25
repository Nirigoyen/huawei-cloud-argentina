output "dify_url" {
  description = "URL para acceder a la UI de Dify"
  value       = "http://${huaweicloud_vpc_eip.dify.address}"
}

output "dify_eip" {
  description = "EIP de la instancia de Dify"
  value       = huaweicloud_vpc_eip.dify.address
}

output "ollama_private_ip" {
  description = "IP privada de la ECS de Ollama (usar como server URL al configurar el provider en Dify)"
  value       = huaweicloud_compute_instance.ollama.access_ip_v4
}

output "rds_private_ip" {
  description = "IP privada de la RDS PostgreSQL"
  value       = huaweicloud_rds_instance.dify.private_ips[0]
}

output "ssh_dify" {
  description = "Comando SSH para conectarse a la ECS de Dify"
  value       = "ssh ubuntu@${huaweicloud_vpc_eip.dify.address}"
}

output "ssh_ollama" {
  description = "Comando SSH para conectarse a la ECS de Ollama (desde dentro del VPC)"
  value       = "ssh ubuntu@${huaweicloud_compute_instance.ollama.access_ip_v4}"
}
