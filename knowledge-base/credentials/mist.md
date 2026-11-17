<!-- n8n built-in node reference: mist | source: https://docs.n8n.io/integrations/builtin/credentials/mist -->

> **Credential-only node:** This node exists only to supply credentials to other nodes.

## Prerequisites

Create a [Mist](https://www.mist.com/) account and organization. Refer to [Create a Mist account and Organization](https://www.mist.com/documentation/create-mist-org/) for detailed instructions.

## Supported authentication methods

- API token

## Related resources

Refer to [Mist's documentation](https://www.mist.com/documentation/mist-api-introduction/) for more information about the service. If you're logged in to your Mist account, go to [https://api.mist.com/api/v1/docs/Home](https://api.mist.com/api/v1/docs/Home) to view the full API documentation.

This is a credential-only node. Refer to [Custom API operations](https://docs.n8n.io/integrations/builtin/custom-api-actions-for-existing-nodes) to learn more. View [example workflows and related content](https://n8n.io/integrations/mist/) on n8n's website.

## Using API token

To configure this credential, you'll need:

- An **API Token**: You can use either a User API token or an Org API token. Refer to [How to generate a user API token](https://www.mist.com/documentation/using-postman/) for instructions on generating a User API token. Refer to [Org API token](https://www.mist.com/documentation/org-api-token/) for instructions on generating an Org API token.
- Select the **Region** you're in. Options include:
    - **Europe**: Select this option if your cloud environment is in any of the EMEA regions.
    - **Global**: Select this option if your cloud environment is in any of the global regions.
