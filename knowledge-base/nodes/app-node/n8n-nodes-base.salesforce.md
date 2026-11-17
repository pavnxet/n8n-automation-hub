<!-- n8n built-in node reference: n8n-nodes-base.salesforce | source: https://docs.n8n.io/integrations/builtin/app-nodes/n8n-nodes-base.salesforce -->

Use the Salesforce node to automate work in Salesforce, and integrate Salesforce with other applications. n8n has built-in support for a wide range of Salesforce features, including creating, updating, deleting, and getting accounts, attachments, cases, and leads, as well as uploading documents. 

On this page, you'll find a list of operations the Salesforce node supports and links to more resources.

> **Credentials:**
> Refer to [Salesforce credentials](https://docs.n8n.io/integrations/builtin/credentials/salesforce) for guidance on setting up authentication.

> **AI tool:** This node can be used as an AI tool. Connect it to the Tools input of an AI Agent node so the agent can call it.

## Operations

* Account
    * Add note to an account
    * Create an account
    * Create a new account, or update the current one if it already exists (upsert)
    * Get an account
    * Get all accounts
    * Returns an overview of account's metadata.
    * Delete an account
    * Update an account
* Attachment
    * Create a attachment
    * Delete a attachment
    * Get a attachment
    * Get all attachments
    * Returns an overview of attachment's metadata.
    * Update a attachment
* Case
    * Add a comment to a case
    * Create a case
    * Get a case
    * Get all cases
    * Returns an overview of case's metadata
    * Delete a case
    * Update a case
* Contact
    * Add lead to a campaign
    * Add note to a contact
    * Create a contact
    * Create a new contact, or update the current one if it already exists (upsert)
    * Delete a contact
    * Get a contact
    * Returns an overview of contact's metadata
    * Get all contacts
    * Update a contact
* Custom Object
    * Create a custom object record
    * Create a new record, or update the current one if it already exists (upsert)
    * Get a custom object record
    * Get all custom object records
    * Delete a custom object record
    * Update a custom object record
* Document
    * Upload a document
* Flow
    * Get all flows
    * Invoke a flow
* Lead
    * Add lead to a campaign
    * Add note to a lead
    * Create a lead
    * Create a new lead, or update the current one if it already exists (upsert)
    * Delete a lead
    * Get a lead
    * Get all leads
    * Returns an overview of Lead's metadata
    * Update a lead
* Opportunity
    * Add note to an opportunity
    * Create an opportunity
    * Create a new opportunity, or update the current one if it already exists (upsert)
    * Delete an opportunity
    * Get an opportunity
    * Get all opportunities
    * Returns an overview of opportunity's metadata
    * Update an opportunity
* Search
    * Execute a SOQL query that returns all the results in a single response
* Task
    * Create a task
    * Delete a task
    * Get a task
    * Get all tasks
    * Returns an overview of task's metadata
    * Update a task
* User
    * Get a user
    * Get all users

## Templates and examples

[Browse Salesforce node documentation integration templates](https://n8n.io/integrations/salesforce) or [search all templates](https://n8n.io/workflows/)

## Working with Salesforce custom fields

To add custom fields to your request:

1. Select **Additional Fields** > **Add Field**.
2. In the dropdown, select **Custom Fields**.

You can then find and add your custom fields.
