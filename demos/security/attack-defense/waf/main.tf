terraform {
  required_providers {
    huaweicloud = {
      source = "huaweicloud/huaweicloud"
    }
  }
}

# postPaid + website="hec-hk" is HuaweiCloud International only (per provider docs).
# In la-south-2 this works for observe mode (detect+log) but protection_mode="block"
# on the policy returns WAF.00013002. Block mode needs prePaid + resource_spec_code
# (monthly commitment). See waf_policy resource when switching to prePaid.
resource "huaweicloud_waf_cloud_instance" "demo" {
  charging_mode = "postPaid"
  website       = "hec-hk"
}

resource "huaweicloud_waf_domain" "domain" {
  depends_on = [huaweicloud_waf_cloud_instance.demo]
  domain     = var.domain_name

  server {
    client_protocol = "HTTP"
    server_protocol = "HTTP"
    address         = var.host_eip
    port            = 80
    type            = "ipv4"
  }

  website_name   = "securityDemo"
  protect_status = 1 # 0=suspended 1=enabled(detect per policy) -1=bypass
  proxy          = true
  charging_mode  = "postPaid"
}
