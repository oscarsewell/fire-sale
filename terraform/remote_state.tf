terraform {
  backend "s3" {
    bucket  = "c23-fire-sale-terraform-state"
    key     = "c23-fire-sale"
    region  = "eu-west-2"
    encrypt = true
  }
}