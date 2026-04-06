#!/bin/bash

set -e

echo "🚀 Setting up ALB for Memory Server..."

# Configuration
MEMORY_SERVER_NAME="memory-server"
HEALTH_CHECK_PATH="/health"
PORT=8000

# Get current instance and VPC info
INSTANCE_ID=$(curl -s http://169.254.169.254/latest/meta-data/instance-id)
VPC_ID=$(aws ec2 describe-instances --instance-ids $INSTANCE_ID --query 'Reservations[0].Instances[0].VpcId' --output text)
SUBNET_IDS=$(aws ec2 describe-subnets --filters "Name=vpc-id,Values=$VPC_ID" "Name=availability-zone,Values=*" --query 'Subnets[].SubnetId' --output text)
SUBNET_ARRAY=($SUBNET_IDS)

echo "📍 Instance ID: $INSTANCE_ID"
echo "🌐 VPC ID: $VPC_ID"
echo "📡 Subnets: ${SUBNET_ARRAY[@]}"

# 1. Create Target Group
echo "📋 Creating target group..."
TARGET_GROUP_ARN=$(aws elbv2 create-target-group \
  --name ${MEMORY_SERVER_NAME}-tg \
  --protocol HTTP \
  --port $PORT \
  --vpc-id $VPC_ID \
  --health-check-protocol HTTP \
  --health-check-port $PORT \
  --health-check-path $HEALTH_CHECK_PATH \
  --health-check-interval-seconds 30 \
  --health-check-timeout-seconds 10 \
  --healthy-threshold-count 2 \
  --unhealthy-threshold-count 3 \
  --matcher HttpCode=200 \
  --query 'TargetGroups[0].TargetGroupArn' \
  --output text 2>/dev/null || echo "Target group might already exist")

if [ "$TARGET_GROUP_ARN" = "Target group might already exist" ]; then
    TARGET_GROUP_ARN=$(aws elbv2 describe-target-groups --names ${MEMORY_SERVER_NAME}-tg --query 'TargetGroups[0].TargetGroupArn' --output text)
fi

echo "✅ Target Group ARN: $TARGET_GROUP_ARN"

# 2. Register instance with target group
echo "🎯 Registering instance with target group..."
aws elbv2 register-targets \
  --target-group-arn $TARGET_GROUP_ARN \
  --targets Id=$INSTANCE_ID,Port=$PORT 2>/dev/null || echo "Instance already registered"

# 3. Create ALB Security Group
echo "🔒 Creating ALB security group..."
ALB_SG_ID=$(aws ec2 create-security-group \
  --group-name ${MEMORY_SERVER_NAME}-alb-sg \
  --description "Security group for Memory Server ALB" \
  --vpc-id $VPC_ID \
  --query 'GroupId' \
  --output text 2>/dev/null || aws ec2 describe-security-groups --filters "Name=group-name,Values=${MEMORY_SERVER_NAME}-alb-sg" --query 'SecurityGroups[0].GroupId' --output text)

# Allow HTTP and HTTPS to ALB
aws ec2 authorize-security-group-ingress \
  --group-id $ALB_SG_ID \
  --protocol tcp \
  --port 80 \
  --cidr 0.0.0.0/0 2>/dev/null || echo "Port 80 rule already exists"

aws ec2 authorize-security-group-ingress \
  --group-id $ALB_SG_ID \
  --protocol tcp \
  --port 443 \
  --cidr 0.0.0.0/0 2>/dev/null || echo "Port 443 rule already exists"

echo "✅ ALB Security Group: $ALB_SG_ID"

# 4. Update EC2 security group to allow ALB traffic
echo "🔧 Updating EC2 security group..."
EC2_SG_ID=$(aws ec2 describe-instances \
  --instance-ids $INSTANCE_ID \
  --query 'Reservations[0].Instances[0].SecurityGroups[0].GroupId' \
  --output text)

# Allow traffic from ALB to EC2
aws ec2 authorize-security-group-ingress \
  --group-id $EC2_SG_ID \
  --protocol tcp \
  --port $PORT \
  --source-group $ALB_SG_ID 2>/dev/null || echo "ALB to EC2 rule already exists"

echo "✅ Updated EC2 security group: $EC2_SG_ID"

# 5. Create ALB (using at least 2 subnets in different AZs)
echo "⚖️ Creating Application Load Balancer..."
ALB_ARN=$(aws elbv2 create-load-balancer \
  --name ${MEMORY_SERVER_NAME}-alb \
  --subnets ${SUBNET_ARRAY[0]} ${SUBNET_ARRAY[1]} \
  --security-groups $ALB_SG_ID \
  --scheme internet-facing \
  --type application \
  --ip-address-type ipv4 \
  --query 'LoadBalancers[0].LoadBalancerArn' \
  --output text 2>/dev/null || aws elbv2 describe-load-balancers --names ${MEMORY_SERVER_NAME}-alb --query 'LoadBalancers[0].LoadBalancerArn' --output text)

echo "✅ ALB ARN: $ALB_ARN"

# 6. Create HTTP listener
echo "👂 Creating HTTP listener..."
aws elbv2 create-listener \
  --load-balancer-arn $ALB_ARN \
  --protocol HTTP \
  --port 80 \
  --default-actions Type=forward,TargetGroupArn=$TARGET_GROUP_ARN 2>/dev/null || echo "Listener already exists"

# Get ALB DNS name
ALB_DNS=$(aws elbv2 describe-load-balancers \
  --load-balancer-arns $ALB_ARN \
  --query 'LoadBalancers[0].DNSName' \
  --output text)

echo ""
echo "🎉 ALB setup complete!"
echo "📍 ALB DNS Name: $ALB_DNS"
echo "🔗 Test URL: http://$ALB_DNS/health"
echo ""
echo "💡 Update your bridge to use: http://$ALB_DNS"
echo ""

# Wait a moment for target registration
echo "⏳ Waiting 30 seconds for target registration..."
sleep 30

# Test the setup
echo "🧪 Testing ALB health..."
if curl -f --connect-timeout 10 "http://$ALB_DNS/health" >/dev/null 2>&1; then
    echo "✅ ALB is working! Your memory server is accessible at: http://$ALB_DNS"
else
    echo "⚠️  ALB health check failed. Checking target health..."
    aws elbv2 describe-target-health --target-group-arn $TARGET_GROUP_ARN --query 'TargetHealthDescriptions[0].TargetHealth.State' --output text
    echo "💡 Target might still be registering. Try the URL in a few minutes."
fi

echo ""
echo "🎯 Your bridge command:"
echo "python http_bridge.py --http-url http://$ALB_DNS --user-id your_username"