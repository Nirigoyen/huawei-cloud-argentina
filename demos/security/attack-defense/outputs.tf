output "host_eip" {
  description = "EIP del host (DVWA)"
  value       = module.ecs.host_eip
}

output "attacker_eip" {
  description = "EIP del attacker"
  value       = module.ecs.attacker_eip
}

output "ssh_to_attacker" {
  description = "Comando para SSH al attacker"
  value       = "ssh root@${module.ecs.attacker_eip}"
}

output "bruteforce_command" {
  description = "Comando para correr el SSH brute-force"
  value       = "python3 /opt/ssh_bruteforce.py"
}

output "sqlmap_command" {
  description = "Comando para correr sqlmap contra DVWA"
  value       = "python3 /opt/sqlmap/sqlmap.py -u http://${module.ecs.host_eip}/vulnerabilities/sqli/?id=1 --dbs --level 3"
}

output "dvwa_url" {
  description = "URL de DVWA (acceso directo por EIP)"
  value       = "http://${module.ecs.host_eip}"
}

output "console_notes" {
  description = "Que revisar en la consola de Huawei Cloud"
  value = join("\n", compact([
    "HSS: alertas de virus (EICAR) y vulnerabilidades en el host.",
    "CES: metricas de consumo del host.",
    var.enable_cfw ? "CFW: attack logs y ACL hits en el firewall." : "",
    var.enable_waf ? "WAF: eventos de ataque L7 en ${var.domain_name}." : "",
  ]))
}
