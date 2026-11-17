<!-- n8n built-in node reference: send-email | source: https://docs.n8n.io/integrations/builtin/credentials/send-email -->

You can use these credentials to authenticate the following nodes:

- [Send Email](https://docs.n8n.io/integrations/builtin/core-nodes/n8n-nodes-base.sendemail)

## Prerequisites

- Create an email account on a service that supports SMTP.
- Some email providers require that you enable or set up outgoing SMTP or generate an app password. Refer to your provider's documentation to see if there are other required steps.

## Supported authentication methods

- SMTP account

## Related resources

Simple Message Transfer Protocol (SMTP) is a standard protocol for sending and receiving email. Most email providers offer instructions on setting up their service with SMTP. Refer to your provider's SMTP instructions.

## Using SMTP account

To configure this credential, you'll need:

- A **User** email address
- A **Password**: This may be the user's password or an app password. Refer to the documentation for your email provider.
- The **Host**: The SMTP host address for your email provider, often formatted as `smtp..com`. Check with your provider.
- A **Port** number: The port depends on the encryption method:
  - Port `465` for SSL/TLS (implicit encryption)
  - Port `587` for STARTTLS (explicit encryption)
  - Port `25` for no encryption (not recommended)
    Check with your email provider for their specific requirements.
- **SSL/TLS**: This toggle controls the encryption method:
  - Turn **ON** for port `465` (uses implicit SSL/TLS encryption)
  - Turn **OFF** for port `587` (uses STARTTLS explicit encryption)
  - Turn **OFF** for port `25` (no encryption)
- **Disable STARTTLS**: When SSL/TLS is disabled, the SMTP server can still try to [upgrade the TCP connection using STARTTLS](https://en.wikipedia.org/wiki/Opportunistic_TLS). Turning this on prevents that behaviour.
- **Client Host Name**: This name identifies the client to the server. May not be required for Gmail, Outlook.com, or Yahoo. Leave this field empty unless your email provider or administrator specifically requests it. If you do need to provide a value, use a fully qualified domain name (FQDN) such as `mail.yourdomain.com`. Avoid generic values like `localhost`.

### Provider instructions

Refer to the quickstart guides for these common email providers.

#### Gmail

Refer to [Gmail](https://docs.n8n.io/integrations/builtin/credentials/sendemail/gmail).

#### Outlook.com

Refer to [Outlook.com](https://docs.n8n.io/integrations/builtin/credentials/sendemail/outlook).

#### Yahoo

Refer to [Yahoo](https://docs.n8n.io/integrations/builtin/credentials/sendemail/yahoo).

### My provider isn't listed

If your email provider isn't listed here, search for `SMTP settings` to find their instructions. (These instructions may also be included with `IMAP settings` or `POP settings`.)

---

## Gmail

## Gmail Send Email credentials

Follow these steps to configure the Send Email credentials with a Gmail account.

### Prerequisites

To follow these instructions, you must first:

1. [Enable 2-step Verification](#enable-2-step-verification) on your Gmail account.
2. [Generate an app password](#generate-an-app-password).

#### Enable 2-step Verification

#### Generate an app password

### Set up the credential

To set up the Send Email credential to use Gmail:

1. Enter your Gmail email address as the **User**.
2. Enter the app password you generated above as the **Password**.
3. Enter `smtp.gmail.com` as the **Host**.
4. For the **Port**:
    - Keep the default `465` for SSL or if you're unsure what to use.
    - Enter `587` for TLS.
5. Turn on the **SSL/TLS** toggle.

Refer to the Outgoing Mail (SMTP) Server settings in [Read Gmail messages on other email clients using POP](https://support.google.com/mail/answer/7104828?hl=en) for more information. If the settings above don't work for you, check with your email administrator.

---

## Outlook.com

## Outlook.com Send Email credentials

> **Feature availability:**
> Microsoft deprecated Basic Authentication and app passwords for SMTP in Exchange Online and Outlook.com. As a result, the Send Email node **cannot connect to Outlook.com or Microsoft 365 accounts** using username/password or app password authentication.
> **To send email from your Outlook.com or Microsoft 365 account, use the [Microsoft Outlook node](https://docs.n8n.io/integrations/builtin/app-nodes/n8n-nodes-base.microsoftoutlook), which uses OAuth 2.0 as required by Microsoft.**
> Refer to [Microsoft's deprecation notice](https://learn.microsoft.com/en-us/exchange/clients-and-mobile-in-exchange-online/deprecation-of-basic-authentication-exchange-online#what-we-are-changing) for more information.

---

## Yahoo

## Yahoo Send Email credentials

Follow these steps to configure the Send Email credentials with a Yahoo account.

### Prerequisites

To follow these instructions, you must first generate an app password:

### Set up the credential

To configure the Send Email credential to use Yahoo Mail:

1. Enter your Yahoo email address as the **User**.
2. Enter the app password you generated above as the **Password**.
3. Enter `smtp.mail.yahoo.com` as the **Host**.
4. For the **Port**:
    - Keep the default `465` for SSL or if you're unsure what to use.
    - Enter `587` for TLS.
5. Turn on the **SSL/TLS** toggle.

Refer to [IMAP server settings for Yahoo Mail](https://help.yahoo.com/kb/sln4075.html) for more information. If the settings above don't work for you, check with your email administrator.
