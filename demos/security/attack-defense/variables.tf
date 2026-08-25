variable "region" {
  description = "Region de Huawei Cloud para el deployment"
  type        = string
  default     = "la-south-2"
}

variable "access_key" {
  description = "Access Key de Huawei Cloud (AK)"
  type        = string
  sensitive   = true
}

variable "secret_key" {
  description = "Secret Key de Huawei Cloud (SK)"
  type        = string
  sensitive   = true
}

variable "ecs_password" {
  description = "Password de admin para las ECS (user: root). 8-32 chars, mayusculas, minusculas, numeros y especiales ~!@#%^*-_=+?"
  type        = string
  sensitive   = true
}

variable "availability_zone" {
  description = "Zona de disponibilidad dentro de la region"
  type        = string
  default     = "la-south-2a"
}

variable "image_name_regex" {
  description = "Regex para buscar la imagen Ubuntu publica via data source"
  type        = string
  default     = "^Ubuntu 24.04"
}

variable "image_id_override" {
  description = "Override del image ID (usar una imagen especifica). Vacio = data source."
  type        = string
  default     = ""
}

variable "host_flavor" {
  description = "Flavor de ECS para el host (DVWA + HSS + CES)"
  type        = string
  default     = "t6.large.1"
}

variable "attacker_flavor" {
  description = "Flavor de ECS para el attacker"
  type        = string
  default     = "t6.large.1"
}

variable "system_disk_type" {
  description = "Tipo de disco del sistema para las ECS"
  type        = string
  default     = "SAS"
}

variable "host_system_disk_size" {
  description = "Tamano del disco del sistema del host (GB)"
  type        = number
  default     = 60
}

variable "attacker_system_disk_size" {
  description = "Tamano del disco del sistema del attacker (GB)"
  type        = number
  default     = 40
}

variable "eip_bandwidth" {
  description = "Ancho de banda de las EIPs en Mbit/s"
  type        = number
  default     = 5
}

variable "enable_cfw" {
  description = "Habilitar Cloud Firewall (CFW Professional — recurso paid)"
  type        = bool
  default     = false
}

variable "enable_waf" {
  description = "Habilitar WAF + DNS (requiere domain_name y public_zone — recurso paid)"
  type        = bool
  default     = false
}

variable "domain_name" {
  description = "Dominio a proteger con WAF (requerido si enable_waf=true)"
  type        = string
  default     = ""
}

variable "public_zone" {
  description = "Zona publica de DNS en Huawei Cloud (requerido si enable_waf=true)"
  type        = string
  default     = ""
}
