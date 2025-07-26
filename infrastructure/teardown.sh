#!/bin/bash

# Teardown script for ScienceBridge Azure App Service
# This script is idempotent - it can be run multiple times safely
# WARNING: This will DELETE all resources - use with caution!

set -e

# Configuration - should match your setup script
RESOURCE_GROUP="rg-sciencebridge"
APP_SERVICE_PLAN="asp-sciencebridge"
APP_NAME="sciencebridge"
ACR_NAME="sciencebridgeacr"
ACR_REGISTRY_URL="sciencebridgeacr.azurecr.io"
IMAGE_NAME="sciencebridge"
SERVICE_PRINCIPAL_NAME="sp-sciencebridge-github"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

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

# Function to print error
print_error() {
    echo -e "${RED}❌ $1${NC}"
}

# Function to confirm action
confirm_action() {
    local message=$1
    local default=${2:-"n"}
    
    if [ "$FORCE_DELETE" = "true" ]; then
        return 0
    fi
    
    echo -e "${YELLOW}$message${NC}"
    read -p "Are you sure? (y/N): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        return 0
    else
        return 1
    fi
}

echo -e "${RED}=== ScienceBridge Azure Resources Teardown ===${NC}"
echo -e "${RED}⚠️  WARNING: This will DELETE all ScienceBridge Azure resources!${NC}"
echo ""

# Check for force flag
if [ "$1" = "--force" ] || [ "$1" = "-f" ]; then
    FORCE_DELETE="true"
    print_warning "Force mode enabled - no confirmations will be asked"
fi

# Check if logged in to Azure
print_step "Checking Azure CLI login status"
if ! az account show > /dev/null 2>&1; then
    print_error "Not logged in to Azure. Please run 'az login' first."
    exit 1
fi
print_success "Azure CLI is logged in"

# Get current subscription
SUBSCRIPTION_ID=$(az account show --query id -o tsv)
SUBSCRIPTION_NAME=$(az account show --query name -o tsv)
print_info "Using subscription: $SUBSCRIPTION_NAME ($SUBSCRIPTION_ID)"

# Final confirmation
if ! confirm_action "This will permanently delete ALL ScienceBridge resources in subscription '$SUBSCRIPTION_NAME'"; then
    echo "Teardown cancelled."
    exit 0
fi

echo ""
echo -e "${RED}🚨 Starting teardown process...${NC}"
echo ""

# Step 1: Delete Web App
print_step "Checking and deleting Web App: $APP_NAME"
if check_resource_exists "webapp" "$APP_NAME" "$RESOURCE_GROUP"; then
    print_info "Deleting Web App '$APP_NAME'..."
    az webapp delete \
        --resource-group "$RESOURCE_GROUP" \
        --name "$APP_NAME" \
        --keep-empty-plan \
        --yes > /dev/null 2>&1
    print_success "Web App '$APP_NAME' deleted"
else
    print_info "Web App '$APP_NAME' does not exist (already deleted)"
fi

# Step 2: Check if App Service Plan has other apps before deleting
print_step "Checking App Service Plan: $APP_SERVICE_PLAN"
if check_resource_exists "appserviceplan" "$APP_SERVICE_PLAN" "$RESOURCE_GROUP"; then
    # Check if there are other apps using this plan
    OTHER_APPS=$(az webapp list --resource-group "$RESOURCE_GROUP" --query "[?appServicePlanId contains('$APP_SERVICE_PLAN')].name" -o tsv | wc -l)
    
    if [ "$OTHER_APPS" -eq 0 ]; then
        print_info "Deleting App Service Plan '$APP_SERVICE_PLAN' (no other apps using it)..."
        az appservice plan delete \
            --resource-group "$RESOURCE_GROUP" \
            --name "$APP_SERVICE_PLAN" \
            --yes > /dev/null 2>&1
        print_success "App Service Plan '$APP_SERVICE_PLAN' deleted"
    else
        print_warning "App Service Plan '$APP_SERVICE_PLAN' has other apps - keeping it"
    fi
else
    print_info "App Service Plan '$APP_SERVICE_PLAN' does not exist (already deleted)"
fi

# Step 3: Delete Azure Container Registry
print_step "Checking and deleting Azure Container Registry: $ACR_NAME"
if check_resource_exists "acr" "$ACR_NAME" ""; then
    if confirm_action "Delete Azure Container Registry '$ACR_NAME' and all its images?"; then
        print_info "Deleting Azure Container Registry '$ACR_NAME'..."
        az acr delete \
            --resource-group "$RESOURCE_GROUP" \
            --name "$ACR_NAME" \
            --yes > /dev/null 2>&1
        print_success "Azure Container Registry '$ACR_NAME' deleted"
    else
        print_warning "Skipping ACR deletion"
    fi
else
    print_info "Azure Container Registry '$ACR_NAME' does not exist (already deleted)"
fi

# Step 4: Delete Service Principal
print_step "Checking and deleting Service Principal: $SERVICE_PRINCIPAL_NAME"
if check_resource_exists "sp" "$SERVICE_PRINCIPAL_NAME" ""; then
    if confirm_action "Delete Service Principal '$SERVICE_PRINCIPAL_NAME'? (This will break GitHub Actions)"; then
        SP_APP_ID=$(az ad sp list --display-name "$SERVICE_PRINCIPAL_NAME" --query "[0].appId" -o tsv)
        print_info "Deleting Service Principal '$SERVICE_PRINCIPAL_NAME' (App ID: $SP_APP_ID)..."
        az ad sp delete --id "$SP_APP_ID" > /dev/null 2>&1
        print_success "Service Principal '$SERVICE_PRINCIPAL_NAME' deleted"
        print_warning "Remember to remove AZURE_CREDENTIALS from your GitHub repository secrets"
    else
        print_warning "Skipping Service Principal deletion"
    fi
else
    print_info "Service Principal '$SERVICE_PRINCIPAL_NAME' does not exist (already deleted)"
fi

# Step 5: Delete Resource Group (optional)
print_step "Checking Resource Group: $RESOURCE_GROUP"
if check_resource_exists "resourcegroup" "$RESOURCE_GROUP" ""; then
    # Check if there are other resources in the resource group
    OTHER_RESOURCES=$(az resource list --resource-group "$RESOURCE_GROUP" --query "length(@)")
    
    if [ "$OTHER_RESOURCES" -eq 0 ]; then
        if confirm_action "Delete empty Resource Group '$RESOURCE_GROUP'?"; then
            print_info "Deleting Resource Group '$RESOURCE_GROUP'..."
            az group delete \
                --resource-group "$RESOURCE_GROUP" \
                --yes \
                --no-wait > /dev/null 2>&1
            print_success "Resource Group '$RESOURCE_GROUP' deletion initiated (running in background)"
        else
            print_warning "Keeping empty Resource Group '$RESOURCE_GROUP'"
        fi
    else
        print_warning "Resource Group '$RESOURCE_GROUP' contains other resources ($OTHER_RESOURCES) - keeping it"
        print_info "To see remaining resources run: az resource list --resource-group $RESOURCE_GROUP --output table"
    fi
else
    print_info "Resource Group '$RESOURCE_GROUP' does not exist (already deleted)"
fi

# Step 6: Clean up - no local files to clean since we don't create them

# Final Summary
echo ""
echo -e "${GREEN}=== TEARDOWN SUMMARY ===${NC}"
echo ""
echo -e "${YELLOW}🗑️  Teardown Results:${NC}"

# Check what's left
echo "   Web App: $(check_resource_exists "webapp" "$APP_NAME" "$RESOURCE_GROUP" && echo "❌ Still exists" || echo "✅ Deleted")"
echo "   App Service Plan: $(check_resource_exists "appserviceplan" "$APP_SERVICE_PLAN" "$RESOURCE_GROUP" && echo "❌ Still exists" || echo "✅ Deleted")"
echo "   Container Registry: $(check_resource_exists "acr" "$ACR_NAME" "" && echo "❌ Still exists" || echo "✅ Deleted")"
echo "   Service Principal: $(check_resource_exists "sp" "$SERVICE_PRINCIPAL_NAME" "" && echo "❌ Still exists" || echo "✅ Deleted")"
echo "   Resource Group: $(check_resource_exists "resourcegroup" "$RESOURCE_GROUP" "" && echo "❌ Still exists" || echo "✅ Deleted/Deleting")"

echo ""
echo -e "${YELLOW}📋 Post-Teardown Tasks:${NC}"
echo "   1. Remove AZURE_CREDENTIALS from GitHub repository secrets"
echo "   2. Remove any custom domains or DNS records"
echo "   3. Cancel any associated billing alerts"
echo "   4. Remove .github/workflows/deploy.yml if no longer needed"
echo "   5. Check for any remaining resources: az resource list --resource-group $RESOURCE_GROUP"

if check_resource_exists "resourcegroup" "$RESOURCE_GROUP" ""; then
    echo ""
    echo -e "${YELLOW}🔍 Remaining Resources Check:${NC}"
    echo "   Run this command to see what's left:"
    echo "   az resource list --resource-group $RESOURCE_GROUP --output table"
fi

echo ""
echo -e "${GREEN}✅ Teardown process completed!${NC}"
echo ""
echo -e "${YELLOW}💡 Tips:${NC}"
echo "   - Resource Group deletion runs in background and may take a few minutes"
echo "   - Check Azure Portal to confirm all resources are deleted"
echo "   - Review your Azure bill to ensure no unexpected charges"
echo ""
echo -e "${RED}⚠️  Remember: This action cannot be undone!${NC}"