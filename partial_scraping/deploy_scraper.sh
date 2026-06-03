# Bash script to build and push Docker image to ECR for a given website scraper

set -e  # Exit if any command fails

if [ -z "$account_number" ] || [ -z "$website_name" ]; then
    echo "Error: account_number and website_name variables required"
    exit 1
fi

aws ecr get-login-password --region eu-west-2 | docker login --username AWS --password-stdin ${account_number}.dkr.ecr.eu-west-2.amazonaws.com

docker buildx build -t fire-sale-prod-lambda-scraper-${website_name}:latest --provenance=false --platform="linux/amd64" .

docker tag fire-sale-prod-lambda-scraper-${website_name}:latest ${account_number}.dkr.ecr.eu-west-2.amazonaws.com/fire-sale-prod-lambda-scraper-${website_name}:latest

docker push ${account_number}.dkr.ecr.eu-west-2.amazonaws.com/fire-sale-prod-lambda-scraper-${website_name}:latest