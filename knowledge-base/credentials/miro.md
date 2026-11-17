<!-- n8n built-in node reference: miro | source: https://docs.n8n.io/integrations/builtin/credentials/miro -->

> **Credential-only node:** This node exists only to supply credentials to other nodes.

## Prerequisites

Create a [Miro](https://miro.com/) account.

## Supported authentication methods

* OAuth2

## Related resources

Refer to [Miro's API documentation](https://developers.miro.com/reference/overview) for more information about the service.

This is a credential-only node. Refer to [Custom API operations](https://docs.n8n.io/integrations/builtin/custom-api-actions-for-existing-nodes) to learn more. View [example workflows and related content](https://n8n.io/integrations/miro/) on n8n's website.

## Using OAuth2

To configure this credential, you'll need a [Miro](https://miro.com/login/) account and app, as well as:

- A **Client ID**: Generated when you create a new OAuth2 application.
- A **Client Secret**: Generated when you create a new OAuth2 application.

Refer to [Miro's API documentation](https://developers.miro.com/reference/overview) for more information about authenticating to the service.

> **n8n Cloud:** Cloud users can connect with the one-click sign-in button instead of entering keys manually.

If you're [self-hosting](https://app.gitbook.com/s/jm0ZYRpZIPWge2ZSiDYO/host-n8n) n8n, you'll need to [create an app](https://developers.miro.com/docs/rest-api-build-your-first-hello-world-app) to configure OAuth2. Refer to [Miro's OAuth documentation](https://developers.miro.com/docs/getting-started-with-oauth) for more information about setting up OAuth2.
