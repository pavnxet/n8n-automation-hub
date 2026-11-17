<!-- n8n built-in node reference: mailchimp | source: https://docs.n8n.io/integrations/builtin/credentials/mailchimp -->

You can use these credentials to authenticate the following nodes:

- [Mailchimp](https://docs.n8n.io/integrations/builtin/app-nodes/n8n-nodes-base.mailchimp)
- [Mailchimp Trigger](https://docs.n8n.io/integrations/builtin/trigger-nodes/n8n-nodes-base.mailchimptrigger)

## Prerequisites

Create a [Mailchimp](https://www.mailchimp.com/) account.

## Supported authentication methods

- API key
- OAuth2

Refer to [Selecting an authentication method](#selecting-an-authentication-method) for guidance on which method to use.

## Related resources

Refer to [Mailchimp's API documentation](https://mailchimp.com/developer/marketing/api/) for more information about the service.

## Using API key

To configure this credential, you'll need:

- An **API Key**: Generate an API key in the [API keys section](https://us1.admin.mailchimp.com/account/api/) of your Mailchimp account. Refer to [Mailchimp's Generate your API key documentation](https://mailchimp.com/developer/marketing/build/get-started/generate-your-api-key) for more detailed instructions.

## Using OAuth2

> **n8n Cloud:** Cloud users can connect with the one-click sign-in button instead of entering keys manually.

If you need to configure OAuth2 from scratch, [register an application](https://mailchimp.com/developer/marketing/build/start-developing/set-up-an-oauth-app). Refer to the [Mailchimp OAuth2 documentation](https://mailchimp.com/developer/marketing/api-concepts/authentication/oauth-2) for more information.

## Selecting an authentication method

Mailchimp suggests using an API key if you're only accessing your own Mailchimp account's data:

> Use an API key if you're writing code that tightly couples _your_ application's data to _your_ Mailchimp account's data. If you ever need to access _someone else's_ Mailchimp account's data, you should be using OAuth 2 ([source](https://mailchimp.com/developer/marketing/api-concepts/authentication))
