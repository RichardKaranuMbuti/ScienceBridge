#!/bin/bash

# Setup script for ScienceBridge Azure App Service
# This script is idempotent - it can be run multiple times safely

set -e

# Configuration
RESOURCE_GROUP="rg-sciencebridge"
APP_SERVICE_PLAN="asp-sciencebridge"
APP_NAME="sciencebridge"
ACR_NAME="sciencebridgeacr"
ACR_REGISTRY_URL="sciencebridgeacr.azurecr.io"
IMAGE_NAME="sciencebridge"
LOCATION="East US"
SERVICE_PRINCIPAL_NAME="sp-sciencebridge-github"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${GREEN}=== Setting up ScienceBridge App Service ===${NC}"

# Function to check if resource exists
check_resource_exists() {
    local resource_type=$1
    local resource_name=$2
    local resource_group=$3
    
    case $resource_type in
        "webapp")
            az webapp show --name "$resource_name" --resource-group "$resource_group" > /dev/null 2>&1
            ;;
        "acr")
            az acr show --name "$resource_name" > /dev/null 2>&1
            ;;
        "appserviceplan")
            az appservice plan show --name "$resource_name" --resource-group "$resource_group" > /dev/null 2>&1
            ;;
        "resourcegroup")
            az group show --name "$resource_group" > /dev/null 2>&1
            ;;
        "sp")
            az ad sp list --display-name "$resource_name" --query "[0].appId" -o tsv | grep -q .
            ;;
    esac
}

# Function to print step
print_step() {
    echo -e "${YELLOW}>>> $1${NC}"
}

# Function to print success
print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

# Function to print info
print_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

# Function to print warning
print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

# Check if logged in to Azure
print_step "Checking Azure CLI login status"
if ! az account show > /dev/null 2>&1; then
    echo -e "${RED}❌ Not logged in to Azure. Please run 'az login' first.${NC}"
    exit 1
fi
print_success "Azure CLI is logged in"

# Get current subscription
SUBSCRIPTION_ID=$(az account show --query id -o tsv)
SUBSCRIPTION_NAME=$(az account show --query name -o tsv)
print_info "Using subscription: $SUBSCRIPTION_NAME ($SUBSCRIPTION_ID)"

# Step 1: Check/Create Resource Group
print_step "Checking Resource Group: $RESOURCE_GROUP"
if check_resource_exists "resourcegroup" "$RESOURCE_GROUP" ""; then
    print_success "Resource Group '$RESOURCE_GROUP' already exists"
else
    print_info "Creating Resource Group '$RESOURCE_GROUP'"
    az group create --name "$RESOURCE_GROUP" --location "$LOCATION"
    print_success "Resource Group '$RESOURCE_GROUP' created"
fi

# Step 2: Check/Create Azure Container Registry
print_step "Checking Azure Container Registry: $ACR_NAME"
if check_resource_exists "acr" "$ACR_NAME" ""; then
    print_success "Azure Container Registry '$ACR_NAME' already exists"
else
    print_info "Creating Azure Container Registry '$ACR_NAME'"
    az acr create \
        --resource-group "$RESOURCE_GROUP" \
        --name "$ACR_NAME" \
        --sku Basic \
        --admin-enabled true \
        --location "$LOCATION"
    print_success "Azure Container Registry '$ACR_NAME' created"
fi

# Step 3: Check/Create App Service Plan
print_step "Checking App Service Plan: $APP_SERVICE_PLAN"
if check_resource_exists "appserviceplan" "$APP_SERVICE_PLAN" "$RESOURCE_GROUP"; then
    print_success "App Service Plan '$APP_SERVICE_PLAN' already exists"
else
    print_info "Creating App Service Plan '$APP_SERVICE_PLAN'"
    az appservice plan create \
        --name "$APP_SERVICE_PLAN" \
        --resource-group "$RESOURCE_GROUP" \
        --sku B1 \
        --is-linux \
        --location "$LOCATION"
    print_success "App Service Plan '$APP_SERVICE_PLAN' created"
fi

# Step 4: Check/Create Web App
print_step "Checking Web App: $APP_NAME"
if check_resource_exists "webapp" "$APP_NAME" "$RESOURCE_GROUP"; then
    print_success "Web App '$APP_NAME' already exists"
else
    print_info "Creating Web App '$APP_NAME'"
    az webapp create \
        --resource-group "$RESOURCE_GROUP" \
        --plan "$APP_SERVICE_PLAN" \
        --name "$APP_NAME" \
        --deployment-container-image-name "$ACR_REGISTRY_URL/$IMAGE_NAME:latest"
    print_success "Web App '$APP_NAME' created"
fi

# Step 5: Check/Create Service Principal
print_step "Checking Service Principal: $SERVICE_PRINCIPAL_NAME"
if check_resource_exists "sp" "$SERVICE_PRINCIPAL_NAME" ""; then
    print_success "Service Principal '$SERVICE_PRINCIPAL_NAME' already exists"
    SP_APP_ID=$(az ad sp list --display-name "$SERVICE_PRINCIPAL_NAME" --query "[0].appId" -o tsv)
    print_info "Service Principal App ID: $SP_APP_ID"
else
    print_info "Creating Service Principal '$SERVICE_PRINCIPAL_NAME'"
    
    # Create service principal with contributor role for the resource group
    SP_DETAILS=$(az ad sp create-for-rbac \
        --name "$SERVICE_PRINCIPAL_NAME" \
        --role contributor \
        --scopes "/subscriptions/$SUBSCRIPTION_ID/resourceGroups/$RESOURCE_GROUP" \
        --json-auth)
    
    SP_APP_ID=$(echo "$SP_DETAILS" | jq -r '.clientId')
    print_success "Service Principal '$SERVICE_PRINCIPAL_NAME' created"
    print_info "Service Principal App ID: $SP_APP_ID"
    
    # Display the credentials for GitHub Secrets (no file created)
    echo ""
    echo -e "${GREEN}=== AZURE_CREDENTIALS for GitHub Secrets ===${NC}"
    echo -e "${YELLOW}Copy the JSON below and paste it as 'AZURE_CREDENTIALS' in your GitHub repository secrets:${NC}"
    echo -e "${RED}⚠️  IMPORTANT: These credentials will only be shown once - copy them now!${NC}"
    echo ""
    echo -e "${BLUE}--- START COPYING FROM HERE ---${NC}"
    echo "$SP_DETAILS"
    echo -e "${BLUE}--- END COPYING HERE ---${NC}"
    echo ""
fi

# Step 6: Assign AcrPush role to Service Principal for ACR
print_step "Configuring Service Principal ACR permissions"
ACR_ID=$(az acr show --name "$ACR_NAME" --query id -o tsv)

# Check if role assignment already exists
if az role assignment list --assignee "$SP_APP_ID" --scope "$ACR_ID" --role "AcrPush" --query "[0].id" -o tsv | grep -q .; then
    print_success "Service Principal already has AcrPush role on ACR"
else
    print_info "Assigning AcrPush role to Service Principal"
    az role assignment create \
        --assignee "$SP_APP_ID" \
        --scope "$ACR_ID" \
        --role "AcrPush"
    print_success "AcrPush role assigned to Service Principal"
fi

# Step 7: Configure Web App for Container
print_step "Configuring Web App for Container deployment"
az webapp config container set \
    --resource-group "$RESOURCE_GROUP" \
    --name "$APP_NAME" \
    --docker-custom-image-name "$ACR_REGISTRY_URL/$IMAGE_NAME:latest" \
    --docker-registry-server-url "https://$ACR_REGISTRY_URL"
print_success "Container configuration updated"

# Step 8: Configure ACR Authentication using Service Principal
print_step "Configuring ACR Authentication with Service Principal"
SP_CLIENT_ID=$(az ad sp list --display-name "$SERVICE_PRINCIPAL_NAME" --query "[0].appId" -o tsv)

# Note: In production, you would get the client secret from your secure storage
# For now, we'll use ACR admin credentials as fallback
ACR_USERNAME=$(az acr credential show --name "$ACR_NAME" --query username -o tsv)
ACR_PASSWORD=$(az acr credential show --name "$ACR_NAME" --query passwords[0].value -o tsv)

az webapp config appsettings set \
    --resource-group "$RESOURCE_GROUP" \
    --name "$APP_NAME" \
    --settings \
        DOCKER_REGISTRY_SERVER_URL="https://$ACR_REGISTRY_URL" \
        DOCKER_REGISTRY_SERVER_USERNAME="$ACR_USERNAME" \
        DOCKER_REGISTRY_SERVER_PASSWORD="$ACR_PASSWORD"
print_success "ACR authentication configured"

# Step 9: Configure Application Settings
print_step "Configuring Application Settings"
az webapp config appsettings set \
    --resource-group "$RESOURCE_GROUP" \
    --name "$APP_NAME" \
    --settings \
        NODE_ENV=production \
        NEXT_TELEMETRY_DISABLED=1 \
        PORT=3000 \
        WEBSITES_PORT=3000 \
        NEXT_PUBLIC_APP_NAME="ScienceBridge" \
        NEXT_PUBLIC_ENVIRONMENT="production" \
        WEBSITES_ENABLE_APP_SERVICE_STORAGE=false \
        DOCKER_ENABLE_CI=true
print_success "Application settings configured"

# Step 10: Enable Container Logging
print_step "Enabling Container Logging"
az webapp log config \
    --resource-group "$RESOURCE_GROUP" \
    --name "$APP_NAME" \
    --docker-container-logging filesystem
print_success "Container logging enabled"

# Step 11: Get App Service URL
print_step "Getting App Service URL"
APP_URL=$(az webapp show --resource-group "$RESOURCE_GROUP" --name "$APP_NAME" --query defaultHostName -o tsv)

# Final Summary
echo -e "\n${GREEN}=== SETUP COMPLETE ===${NC}"
echo -e "${GREEN}🎉 ScienceBridge App Service setup completed successfully!${NC}"
echo ""
echo -e "${YELLOW}📋 Configuration Summary:${NC}"
echo "   Resource Group: $RESOURCE_GROUP"
echo "   App Service Plan: $APP_SERVICE_PLAN"
echo "   Web App: $APP_NAME"
echo "   Container Registry: $ACR_NAME"
echo "   Image: $ACR_REGISTRY_URL/$IMAGE_NAME:latest"
echo "   Service Principal: $SERVICE_PRINCIPAL_NAME"
echo ""
echo -e "${YELLOW}🌐 App Service URL:${NC}"
echo "   https://$APP_URL"
echo ""
echo -e "${YELLOW}🔑 GitHub Actions Setup:${NC}"
SP_EXISTS=$(check_resource_exists "sp" "$SERVICE_PRINCIPAL_NAME" "" && echo "true" || echo "false")
if [ "$SP_EXISTS" = "false" ]; then
    echo "   1. Copy the AZURE_CREDENTIALS JSON displayed above to your GitHub Secrets"
    echo "   2. Set up the GitHub Actions workflow using the provided YAML file"
    echo "   3. Configure any additional secrets (API URLs, etc.)"
else
    echo "   Service Principal already existed - use existing GitHub secrets or recreate if needed"
    echo ""
    echo -e "${YELLOW}   Existing Service Principal found. To recreate credentials:${NC}"
    echo "   1. Delete the existing SP: az ad sp delete --display-name $SERVICE_PRINCIPAL_NAME"
    echo "   2. Re-run this setup script to get new credentials"
fi
echo ""
echo -e "${YELLOW}🔍 Useful Commands:${NC}"
echo "   Check app status: az webapp show --resource-group $RESOURCE_GROUP --name $APP_NAME"
echo "   View logs: az webapp log tail --resource-group $RESOURCE_GROUP --name $APP_NAME"
echo "   Restart app: az webapp restart --resource-group $RESOURCE_GROUP --name $APP_NAME"
echo "   Test ACR login: az acr login --name $ACR_NAME"
echo ""
echo -e "${YELLOW}📝 Next Steps:${NC}"
echo "1. Add the service principal credentials to GitHub Secrets"
echo "2. Set up the GitHub Actions workflow"
echo "3. Build and push your Docker image using the workflow"
echo "4. Configure custom domain if needed"
echo "5. Set up any additional environment variables"
echo ""
echo -e "${GREEN}✅ Setup completed successfully!${NC}"