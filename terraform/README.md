## Terraform remote state setup

- Ensure you are in the `/terraform` directory
- Run `terraform init`
- At the beginning of the output, you should see:

> **Successfully configured the backend "s3"! Terraform will automatically use this backend unless the backend configuration changes.**

- All sorted! You are now using the `c23-fire-sale` remote state on the `c23-fire-sale-terraform-state` S3 bucket.
