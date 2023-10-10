#!/bin/bash

set -o errexit
set -o pipefail
set -o nounset
set -o xtrace # For debugging

###################
# REQUIRED ENV VARIABLES:
#
# PROJECT
# AZURE_ENV_NAME
# AZURE_LOCATION
# AZURE_SUBSCRIPTION_ID
# AZURE_PRINCIPAL_ID
# AZURE_AUTH_CLIENT_ID
# APP_WHITELIST_IP

#####################
# DEPLOY ARM TEMPLATE

# Set account to where ARM template will be deployed to
echo "Deploying to Subscription: $AZURE_SUBSCRIPTION_ID"
az account set --subscription "$AZURE_SUBSCRIPTION_ID"

arm_output=""

# Create resource group
resource_group_name="$PROJECT-$AZURE_ENV_NAME-rg"
echo "Creating resource group: $resource_group_name"
az group create --name "$resource_group_name" --location "$AZURE_LOCATION" --tags Environment="$AZURE_ENV_NAME"

# By default, set all KeyVault permission to deployer
# Retrieve KeyVault User Id
kv_owner_object_id=$(az ad signed-in-user show --output json | jq -r '.id')


# Validate arm template
echo "Validating deployment"
arm_output=$(az deployment group validate \
    --template-file "./infra/main.bicep" \
    --resource-group "$resource_group_name" \
    --parameters location="${AZURE_LOCATION}" environmentName="${AZURE_ENV_NAME}" \
        principalId="${AZURE_PRINCIPAL_ID}" authClientId="${AZURE_AUTH_CLIENT_ID}" \
        appWhitelistIp="${APP_WHITELIST_IP}" \
    --output json)

########################
# DEPLOY ARM TEMPLATE

echo "Deploying resources into $resource_group_name"
arm_output=$(az deployment group create \
    --template-file "./infra/main.bicep" \
    --resource-group "$resource_group_name" \
    --parameters location="${AZURE_LOCATION}" environmentName="${AZURE_ENV_NAME}" \
        principalId="${AZURE_PRINCIPAL_ID}" authClientId="${AZURE_AUTH_CLIENT_ID}" \
        appWhitelistIp="${APP_WHITELIST_IP}" \
    --output json)

if [[ -z $arm_output ]]; then
    echo >&2 "ARM deployment failed."
    exit 1
fi
