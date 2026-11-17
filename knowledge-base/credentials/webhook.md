<!-- n8n built-in node reference: webhook | source: https://docs.n8n.io/integrations/builtin/credentials/webhook -->

You can use these credentials to authenticate the following nodes:

* [Webhook](https://docs.n8n.io/integrations/builtin/core-nodes/n8n-nodes-base.webhook)

## Prerequisites

You must use the authentication method required by the app or service you want to query.

## Supported authentication methods

* Basic auth
* Header auth
* JWT auth
* None

> **Basic auth:** Uses username and password.

> **Header auth:** Send an `Authorization` header (or a custom header) with the credential value.

## Using JWT auth

[**JWT Auth**](https://jwt.io/introduction/) is a method of authentication that uses JSON Web Tokens (JWT) to digitally sign data. This authentication method uses the **JWT credential** and can use either a **Passphrase** or **PEM Key** as key type. Refer to [JWT credential](https://docs.n8n.io/integrations/builtin/credentials/jwt) for more information.
