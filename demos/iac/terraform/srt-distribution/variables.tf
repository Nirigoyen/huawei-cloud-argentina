## Huawei Cloud credentials

variable "huaweicloud_access_key" {
  description = "Huawei Cloud access key (AK)."
  type        = string
  sensitive   = true
}

variable "huaweicloud_secret_key" {
  description = "Huawei Cloud secret key (SK)."
  type        = string
  sensitive   = true
}

variable "huaweicloud_region" {
  description = "Huawei Cloud region. Set to your own region."
  type        = string
  default     = "la-south-2"
}

## ECS

variable "ecs_password" {
  description = "Root password for all ECS instances. Must be 8-26 chars, mixed case + digits + special."
  type        = string
  sensitive   = true
}

variable "ecs_flavor_id" {
  description = "ECS flavor ID. Exact IDs vary by region and availability — check the flavor list for your region."
  type        = string
  default     = "c6.xlarge.2"
}

variable "image_name" {
  description = "OS image name (matched via name_regex)."
  type        = string
  default     = "Ubuntu 22.04 server"
}

variable "availability_zone" {
  description = "Availability zone. Leave empty to let the provider pick one."
  type        = string
  default     = null
}

variable "ssh_public_key" {
  description = "SSH public key (OpenSSH format) to inject into all instances."
  type        = string
}

variable "ssh_source_cidr" {
  description = "CIDR allowed to SSH into instances. Restrict to your IP in production."
  type        = string
  default     = "0.0.0.0/0"
}

## Project

variable "project_name" {
  description = "Prefix for all resource names."
  type        = string
  default     = "srt-poc"
}

variable "vpc_cidr" {
  description = "VPC CIDR block."
  type        = string
  default     = "10.0.0.0/24"
}

## SRT

variable "consumer_count" {
  description = "Number of SRT consumers on the receiver node (half go to each channel)."
  type        = number
  default     = 100
}

variable "srt_latency_us" {
  description = "SRT latency in microseconds."
  type        = number
  default     = 2000000
}

## SWR / naming

variable "swr_org" {
  description = "SWR organization name (used in docs / future image push)."
  type        = string
  default     = "srt-poc"
}

## Dashboard

variable "dashboard_title" {
  description = "Title shown in the relay web dashboard."
  type        = string
  default     = "SRT Distribution Control"
}
