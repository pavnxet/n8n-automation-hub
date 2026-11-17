<!-- n8n built-in node reference: imap | source: https://docs.n8n.io/integrations/builtin/credentials/imap -->

You can use these credentials to authenticate the following nodes:

- [IMAP Email](https://docs.n8n.io/integrations/builtin/core-nodes/n8n-nodes-base.emailimap)

## Prerequisites

Create an email account on a service with IMAP support.

## Supported authentication methods

- User account

## Related resources

Internet Message Access Protocol (IMAP) is a standard protocol for receiving email. Most email providers offer instructions on setting up their service with IMAP; refer to your provider's IMAP instructions.

## Using user account

To configure this credential, you'll need:

- A **User** name: The email address you're retrieving email for.
- A **Password**: Either the password you use to check email or an app password. Your provider will tell you whether to use your own password or to generate an app password.
- A **Host**: The IMAP host address for your email provider, often formatted as `imap..com`. Check with your provider.
- A **Port** number: The default is port `993`. Use this port unless your provider or email administrator tells you to use something different.

Choose whether to use **SSL/TLS** and whether to **Allow Self-Signed Certificates**.

### Provider instructions

Refer to the quickstart guides for these common email providers.

#### Gmail

Refer to [Gmail](https://docs.n8n.io/integrations/builtin/credentials/imap/gmail).

#### Outlook.com

Refer to [Outlook.com](https://docs.n8n.io/integrations/builtin/credentials/imap/outlook).

#### Yahoo

Refer to [Yahoo](https://docs.n8n.io/integrations/builtin/credentials/imap/yahoo).

### My provider isn't listed

If your email provider isn't listed here, search for their `IMAP settings` or `IMAP instructions`.

---

## Gmail

## Gmail IMAP credentials

Follow these steps to configure the IMAP credentials with a Gmail account.

### Prerequisites

To follow these instructions, you must first:

1. [Enable 2-step Verification](#enable-2-step-verification) on your Gmail account.
2. [Generate an app password](#generate-an-app-password).

#### Enable 2-step Verification

#### Generate an app password

### Set up the credential

To set up the IMAP credential with a Gmail account, use these settings:

1. Enter your Gmail email address as the **User**.
2. Enter the app password you generated above as the **Password**.
3. Enter `imap.gmail.com` as the **Host**.
4. For the **Port**, keep the default port number of `993`. Check with your email administrator if this port doesn't work.
5. Turn on the **SSL/TLS** toggle.
6. Check with your email administrator about whether to **Allow Self-Signed Certificates**.

Refer to [Add Gmail to another client](https://support.google.com/mail/answer/7126229?hl=en) for more information. For personal Google accounts, IMAP access is always enabled. Google removed the **Enable IMAP** / **Disable IMAP** toggle in January 2025. If you're using a Google Workspace account and IMAP doesn't work, check with your email administrator whether they allow IMAP access for your account.

---

## Outlook.com

> **Feature availability:**
> Microsoft deprecated Basic Authentication for IMAP in Exchange Online and
> Outlook.com from October 1, 2022. As a result, the IMAP node **can't connect to Outlook.com or
> Microsoft 365 accounts**. App passwords are not a workaround for this
> restriction.
> **Use the [Microsoft Outlook node](https://docs.n8n.io/integrations/builtin/app-nodes/n8n-nodes-base.microsoftoutlook)
> instead.** It uses OAuth 2.0, which Microsoft now requires for mail access.
> Refer to [Microsoft's deprecation notice](https://learn.microsoft.com/en-us/exchange/clients-and-mobile-in-exchange-online/deprecation-of-basic-authentication-exchange-online#what-we-are-changing)
> for more information.

## Outlook.com IMAP credentials

IMAP access for Outlook.com and Microsoft 365 accounts is no longer supported in n8n due to Microsoft's deprecation of Basic Authentication for Exchange Online and Outlook.com from October 1, 2022. You can't use IMAP (with a regular password or app password) to connect to Outlook.com or Microsoft 365 accounts.

To replace IMAP triggers for incoming email, use the [Microsoft Outlook Trigger node](https://docs.n8n.io/integrations/builtin/trigger-nodes/n8n-nodes-base.microsoftoutlooktrigger), which supports the Message Received event.

For general Microsoft Outlook automation, use the [Microsoft Outlook node](https://docs.n8n.io/integrations/builtin/app-nodes/n8n-nodes-base.microsoftoutlook), which uses OAuth 2.0 as required by Microsoft.

For more information, refer to [Microsoft's deprecation notice](https://learn.microsoft.com/en-us/exchange/clients-and-mobile-in-exchange-online/deprecation-of-basic-authentication-exchange-online#what-we-are-changing).

---

## Yahoo

## Yahoo IMAP credentials

Follow these steps to configure the IMAP credentials with a Yahoo account.

### Prerequisites

To follow these instructions, you must first generate an app password:

### Set up the credential

To set up the IMAP credential with a Yahoo Mail account, use these settings:

1. Enter your Yahoo email address as the **User**.
2. Enter the app password you generated above as the **Password**.
3. Enter `imap.mail.yahoo.com` as the **Host**.
4. Keep the default **Port** number of `993`. Check with your email administrator if this port doesn't work.
5. Turn on the **SSL/TLS** toggle.
6. Check with your email administrator about whether to **Allow Self-Signed Certificates**.

Refer to [Set up IMAP for Yahoo mail account](https://help.yahoo.com/kb/sln4075.html) for more information.
