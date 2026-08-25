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

variable "ssh_public_key" {
  description = "Clave publica SSH para acceder a las ECS (contenido de ~/.ssh/id_rsa.pub)"
  type        = string
  sensitive   = true
}

variable "availability_zone" {
  description = "Zona de disponibilidad dentro de la region"
  type        = string
  default     = "la-south-2a"
}

variable "dify_version" {
  description = "Version de Dify a deployar (tag de git del repo langgenius/dify)"
  type        = string
  default     = "1.17.0"
}

variable "dify_flavor" {
  description = "Flavor de ECS para Dify (vCPU/RAM)"
  type        = string
  default     = "s6.large.4"
}

variable "ollama_flavor" {
  description = "Flavor de ECS para Ollama (vCPU/RAM)"
  type        = string
  default     = "s6.large.4"
}

variable "rds_flavor" {
  description = "Flavor de RDS para PostgreSQL"
  type        = string
  default     = "rds.pg.n1.large.2"
}

variable "rds_password" {
  description = "Password del usuario admin (root) de la RDS PostgreSQL"
  type        = string
  sensitive   = true
}

variable "eip_bandwidth" {
  description = "Ancho de banda de la EIP de Dify en Mbit/s"
  type        = number
  default     = 5
}
