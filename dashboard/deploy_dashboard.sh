# Bash script to build and push Docker image to ECR for the dashboard

set -e  # Exit if any command fails

# Always build from the project root regardless of where this script is called from
cd "$(dirname "$0")/.."

if [ -z "$account_number" ]; then
    echo "Error: account_number variable required"
    exit 1
fi

aws ecr get-login-password --region eu-west-2 | docker login --username AWS --password-stdin ${account_number}.dkr.ecr.eu-west-2.amazonaws.com

docker buildx build -f dashboard/Dockerfile -t c23-fire-sale-prod-dashboard:latest --provenance=false --platform="linux/amd64" .

docker tag c23-fire-sale-prod-dashboard:latest ${account_number}.dkr.ecr.eu-west-2.amazonaws.com/c23-fire-sale-prod-dashboard:latest

docker push ${account_number}.dkr.ecr.eu-west-2.amazonaws.com/c23-fire-sale-prod-dashboard:latest
