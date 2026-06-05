# Terraform Setup & Deployment

## Prerequisites

- Terraform >= 1.0 installed
- AWS CLI configured with credentials (aws configure)
- AWS account with appropriate permissions (IAM, Lambda, RDS, EC2, Step Functions, SQS, etc.)
- Access to the `c23-fire-sale-terraform-state` S3 bucket for remote state

## Initial Setup

### 1. Initialize Terraform Remote State

```bash
cd terraform
terraform init
```

You should see:
> **Successfully configured the backend "s3"! Terraform will automatically use this backend unless the backend configuration changes.**

This configures Terraform to use the `c23-fire-sale` remote state on the `c23-fire-sale-terraform-state` S3 bucket.

### 2. Configure Variables

Copy `terraform.tfvars.example` to `terraform.tfvars` (if it exists), or create one with the required variables:

```bash
cat > terraform.tfvars << EOF
cohort                         = "c23"
project_name                   = "fire-sale"
environment                    = "prod"
rds_instance_class             = "db.t4g.micro"
rds_db_name                    = "fire_sale"
rds_master_username            = "postgres"
discord_alert_queue_arn        = "arn:aws:sqs:eu-west-2:129033205317:c23-fire-sale-prod-discord-notifications"
EOF
```

**Key Variables:**
- `cohort`: AWS resource naming prefix (e.g., "c23")
- `project_name`: Project identifier (e.g., "fire-sale")
- `environment`: Deployment environment (e.g., "prod")
- `discord_alert_queue_arn`: SQS queue ARN for notifications
- `rds_instance_class`: RDS instance type (recommended: `db.t4g.micro`)
- `rds_db_name`: PostgreSQL database name
- `rds_master_username`: RDS master user

## Creating Infrastructure

### 1. Plan the Deployment

```bash
terraform plan -out=tfplan
```

Review the planned changes to ensure they match your expectations.

### 2. Apply the Configuration

```bash
terraform apply tfplan
```

Or for quick deployments:

```bash
terraform apply
```

### 3. Monitor the Deployment

The Terraform apply will create:
- **VPC Networking**: Security groups, network interfaces, Elastic IPs
- **Lambda Functions**: 6 functions (3 scrapers, cleaning, tracking, notifications)
- **RDS Database**: PostgreSQL 16 instance on db.t4g.micro
- **Step Functions**: Orchestration state machine
- **IAM Roles & Policies**: Execution roles with appropriate permissions
- **Secrets Manager**: Database credentials
- **SQS**: Queue references for notifications

## Infrastructure Details

### Lambda Functions

| Function | Purpose | Deployment |
|----------|---------|-----------|
| `scraper-overclockers` | Scrape overclockers.co.uk | ECR Docker image |
| `scraper-ebuyer` | Scrape ebuyer.co.uk | ECR Docker image |
| `scraper-awd-it` | Scrape awd-it.com | ECR Docker image |
| `lambda-cleaning` | Clean & validate scraped data | ECR Docker image |
| `tracked-product-checker` | Query tracked products from RDS | ECR Docker image |
| `lambda-determine-notification` | Determine if notifications needed | ECR Docker image |

All Lambdas are deployed in the c23-VPC with:
- VPC security group: `c23-fire-sale-prod-lambda`
- Subnets: 3 public subnets (eu-west-2a, eu-west-2b, eu-west-2c)
- Elastic IPs: Assigned for stable outbound connectivity
- Timeout: 60 seconds
- Memory: 256-512 MB (varies by function)

### RDS Database

- **Engine**: PostgreSQL 16
- **Instance**: db.t4g.micro
- **Storage**: 20 GB
- **Backup**: Automated snapshots
- **Security**: Encryption enabled, IAM database auth enabled
- **Credentials**: Managed by Secrets Manager

### Step Functions

**Workflow:**
1. GetTrackedProducts (Query RDS)
2. ScrapeWebsites (Parallel: 3 scrapers)
3. CleanData (Validate & normalise)
4. DetermineNotification (Check thresholds)
5. CheckNotificationStatus (Map over products)
6. SendEmails (SES notifications)
