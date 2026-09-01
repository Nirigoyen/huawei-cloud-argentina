terraform {
  required_version = ">= 1.5"

  required_providers {
    huaweicloud = {
      source  = "huaweicloud/huaweicloud"
      version = "~> 1.97"
    }
  }
}

provider "huaweicloud" {
  region     = var.huaweicloud_region
  access_key = var.huaweicloud_access_key
  secret_key = var.huaweicloud_secret_key
}

locals {
  prefix = var.project_name

  # De-branded index.html with dashboard title substituted at plan time
  index_html = replace(
    file("${path.module}/scripts/index.html"),
    "__DASHBOARD_TITLE__",
    var.dashboard_title,
  )
}
