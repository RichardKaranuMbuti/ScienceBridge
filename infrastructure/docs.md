To generate the AZURE_CREDENTIALS secret, you need to create an Azure Service Principal. Here's how to do it:
Method 1: Using Azure CLI (Recommended)

Login to Azure CLI:
bashaz login

Create a Service Principal:
bashaz ad sp create-for-rbac --name "github-actions-recruitra" --role contributor --scopes /subscriptions/{subscription-id} --sdk-auth
Replace {subscription-id} with your actual Azure subscription ID. You can get it with:
bashaz account show --query id -o tsv

The command will output JSON like this:
json{
  "clientId": "xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx",
  "clientSecret": "xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx",
  "subscriptionId": "xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx",
  "tenantId": "xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx"
}