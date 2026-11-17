<!-- n8n built-in node reference: n8n-nodes-base.microsoftoutlook | source: https://docs.n8n.io/integrations/builtin/app-nodes/n8n-nodes-base.microsoftoutlook -->

Use the Microsoft Outlook node to automate work in Microsoft Outlook, and integrate Microsoft Outlook with other applications. n8n has built-in support for a wide range of Microsoft Outlook features, including creating, updating, deleting, and getting folders, messages, and drafts. 

On this page, you'll find a list of operations the Microsoft Outlook node supports and links to more resources.

> **Credentials:**
> This node's **Authentication** dropdown offers three options:
> - **Outlook OAuth2**: the Microsoft Outlook-specific OAuth2 credential (default).
> - **Microsoft OAuth2 (Graph)**: a generic Microsoft Graph credential that you can reuse across other Microsoft nodes. When you select this option, make sure you grant the credential the scopes this node needs (for example, `Mail.ReadWrite`, `Mail.Send`, `Calendars.ReadWrite`, and `Contacts.ReadWrite`).
> - **Microsoft Entra Service Principal (App-Only)**: app-only access through a Microsoft Entra app registration, with no signed-in user, available from version 2 of the node. Refer to [Microsoft Entra Service Principal credentials](https://docs.n8n.io/integrations/builtin/credentials/microsoftentraserviceprincipal) for setup and required application permissions.
> Refer to [Microsoft credentials](https://docs.n8n.io/integrations/builtin/credentials/microsoft) for guidance on setting up authentication.

> **Government Cloud Support:**
> If you're using a government cloud tenant (US Government, US Government DOD, or China), make sure to select the appropriate **Microsoft Graph API Base URL** in your Microsoft credentials configuration.

> **AI tool:** This node can be used as an AI tool. Connect it to the Tools input of an AI Agent node so the agent can call it.

## Operations

* Calendar
	* Create
	* Delete
	* Get
	* Get Many
	* Update
* Contact
	* Create
	* Delete
	* Get
	* Get Many
	* Update
* Draft
	* Create
	* Delete
	* Get
	* Send
	* Update
* Event
	* Create
	* Delete
	* Get
	* Get Many
	* Update
* Folder
	* Create
	* Delete
	* Get
	* Get Many
	* Update
* Folder Message
    * Get Many
* Message
	* Delete
	* Get
	* Get Many
	* Move
	* Reply
	* Send
	* Send and Wait for Response
	* Update
* Message Attachment
	* Add
	* Download
	* Get
	* Get Many

## Templates and examples

[Browse Microsoft Outlook node documentation integration templates](https://n8n.io/integrations/microsoft-outlook) or [search all templates](https://n8n.io/workflows/)

## Related resources

Refer to [Outlook's API documentation](https://learn.microsoft.com/en-us/outlook/rest/get-started) for more information about the service.
