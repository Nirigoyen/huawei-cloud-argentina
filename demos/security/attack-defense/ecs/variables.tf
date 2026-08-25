variable "availability_zone" {
  type = string
}

variable "image_id" {
  type = string
}

variable "ecs_password" {
  type      = string
  sensitive = true
}

variable "host_flavor" {
  type = string
}

variable "attacker_flavor" {
  type = string
}

variable "system_disk_type" {
  type = string
}

variable "host_system_disk_size" {
  type = number
}

variable "attacker_system_disk_size" {
  type = number
}

variable "eip_bandwidth" {
  type = number
}

variable "host_sg_id" {
  type = string
}

variable "attacker_sg_id" {
  type = string
}

variable "host_subnet_id" {
  type = string
}

variable "attacker_subnet_id" {
  type = string
}
