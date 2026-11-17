<!-- n8n built-in node reference: philipshue | source: https://docs.n8n.io/integrations/builtin/credentials/philipshue -->

You can use these credentials to authenticate the following nodes:

- [Philips Hue](https://docs.n8n.io/integrations/builtin/app-nodes/n8n-nodes-base.philipshue)

## Prerequisites

Create a [Philips Hue](https://www.philips-hue.com/en-us) account.

## Supported authentication methods

- OAuth2

## Related resources

Refer to [Philips Hue's CLIP API documentation](https://developers.meethue.com/develop/hue-api-v2/api-reference/) for more information about the service.

## Using OAuth2

> **n8n Cloud:** Cloud users can connect with the one-click sign-in button instead of entering keys manually.

If you're using the built-in OAuth connection, you don't need to enter an **APP ID**.

If you need to configure OAuth2 from scratch, you'll need a [Philips Hue developer](https://developers.meethue.com/) account

Create a new remote app on the [Add new Hue Remote API app](https://developers.meethue.com/add-new-hue-remote-api-app/) page.

Use these settings for your app:

- Copy the **OAuth Callback URL** from n8n and add it as a **Callback URL**.
- Copy the **AppId**, **ClientId**, and **ClientSecret** and enter these in the corresponding fields in n8n.
