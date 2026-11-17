<!-- n8n built-in node reference: n8n-nodes-base.linkedin | source: https://docs.n8n.io/integrations/builtin/app-nodes/n8n-nodes-base.linkedin -->

Use the LinkedIn node to automate work in LinkedIn, and integrate LinkedIn with other applications. n8n supports creating posts.

On this page, you'll find a list of operations the LinkedIn node supports and links to more resources.

> **Credentials:**
> Refer to [LinkedIn credentials](https://docs.n8n.io/integrations/builtin/credentials/linkedin) for guidance on setting up authentication.

> **AI tool:** This node can be used as an AI tool. Connect it to the Tools input of an AI Agent node so the agent can call it.

## Operations

* Post
    * Create

## Parameters

* **Post As**: choose whether to post as a **Person** or **Organization**.
* **Person Name or ID** and **Organization URN**: enter an identifier for the person or organization.

	
> **Note:** Posting as organization If posting as an Organization enter the organization number in the URN field. For example, 03262013 not urn:li:company:03262013 .

	
* **Text**: the post contents.
* **Media Category**: use this when including images or article URLs in your post.

## Templates and examples

[Browse LinkedIn node documentation integration templates](https://n8n.io/integrations/linkedin) or [search all templates](https://n8n.io/workflows/)

## Related resources

Refer to [LinkedIn's API documentation](https://learn.microsoft.com/en-us/linkedin/) for more information about the service.
