<!-- n8n built-in node reference: n8n-nodes-base.microsoftexcel | source: https://docs.n8n.io/integrations/builtin/app-nodes/n8n-nodes-base.microsoftexcel -->

Use the Microsoft Excel (OneDrive) node to automate work in Microsoft Excel, and integrate Microsoft Excel with other applications. n8n has built-in support for a wide range of Microsoft Excel features, including adding and retrieving lists of table data, and workbooks, as well as getting worksheets. The node operates on workbooks stored in OneDrive.

On this page, you'll find a list of operations the Microsoft Excel (OneDrive) node supports and links to more resources.

> **Credentials:**
> This node's **Authentication** dropdown offers three options:
> - **Excel OAuth2**: the Microsoft Excel-specific OAuth2 credential (default).
> - **Microsoft OAuth2 (Graph)**: a generic Microsoft Graph credential that you can reuse across other Microsoft nodes. When you select this option, make sure you grant the credential the scopes this node needs (for example, `Files.ReadWrite`, or `Files.ReadWrite.All` if that's the permission your administrator has consented).
> - **Microsoft Entra Service Principal (App-Only)**: app-only access through a Microsoft Entra app registration, with no signed-in user, available from version 2 of the node. Refer to [Microsoft Entra Service Principal credentials](https://docs.n8n.io/integrations/builtin/credentials/microsoftentraserviceprincipal) for setup and required application permissions.
> Refer to [Microsoft credentials](https://docs.n8n.io/integrations/builtin/credentials/microsoft) for guidance on setting up authentication.

> **Government Cloud Support:**
> If you're using a government cloud tenant (US Government, US Government DOD, or China), make sure to select the appropriate **Microsoft Graph API Base URL** in your Microsoft credentials configuration.

> **AI tool:** This node can be used as an AI tool. Connect it to the Tools input of an AI Agent node so the agent can call it.

## Operations

* Table
    * Adds rows to the end of the table
    * Retrieve a list of table columns
    * Retrieve a list of table rows
    * Looks for a specific column value and then returns the matching row
* Workbook
    * Adds a new worksheet to the workbook.
    * Get data of all workbooks
* Worksheet
    * Get all worksheets
    * Get worksheet content

## Templates and examples

[Browse Microsoft Excel (OneDrive) node documentation integration templates](https://n8n.io/integrations/microsoft-excel) or [search all templates](https://n8n.io/workflows/)
