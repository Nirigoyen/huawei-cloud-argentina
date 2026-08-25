terraform {
  required_providers {
    huaweicloud = {
      source = "huaweicloud/huaweicloud"
    }
  }
}

data "huaweicloud_dns_zones" "zone" {
  zone_type = "public"
  name      = var.dns_zone_name
}

resource "huaweicloud_dns_recordset" "record" {
  zone_id = data.huaweicloud_dns_zones.zone.zones[0].id
  type    = "CNAME"
  name    = var.domain_name
  records = ["${var.waf_access_code}.vip1.huaweicloudwaf.com"]
}
