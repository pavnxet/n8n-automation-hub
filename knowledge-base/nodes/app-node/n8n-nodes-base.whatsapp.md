<!-- n8n built-in node reference: n8n-nodes-base.whatsapp | source: https://docs.n8n.io/integrations/builtin/app-nodes/n8n-nodes-base.whatsapp -->

Use the WhatsApp Business Cloud node to automate work in WhatsApp Business, and integrate WhatsApp Business with other applications. n8n has built-in support for a wide range of WhatsApp Business features, including sending messages, and uploading, downloading, and deleting media. 

On this page, you'll find a list of operations the WhatsApp Business Cloud node supports and links to more resources.

> **Credentials:**
> Refer to [WhatsApp Business Cloud credentials](https://docs.n8n.io/integrations/builtin/credentials/whatsapp) for guidance on setting up authentication.

## Operations

* Message
	* Send
	* Send and Wait for Response
	* Send Template
* Media
	* Upload
	* Download
	* Delete

## Templates and examples

[Browse WhatsApp Business Cloud integration templates](https://n8n.io/integrations/whatsapp-business-cloud) or [search all templates](https://n8n.io/workflows/)

## Related resources

Refer to [WhatsApp Business Platform's Cloud API documentation](https://developers.facebook.com/docs/whatsapp/cloud-api) for details about the operations.

## Common issues

For common errors or issues and suggested resolution steps, refer to [Common Issues](https://docs.n8n.io/integrations/builtin/app-nodes/n8n-nodes-base.whatsapp/common-issues).

---

## WhatsApp Business Cloud node common issues

## WhatsApp Business Cloud node common issues

Here are some common errors and issues with the [WhatsApp Business Cloud node](https://docs.n8n.io/integrations/builtin/app-nodes/n8n-nodes-base.whatsapp) and steps to resolve or troubleshoot them.

### Bad request - please check your parameters

This error occurs when WhatsApp Business Cloud rejects your request because of a problem with its parameters. It's common to see this when using the **Send Template** operation if the data you send doesn't match the format of your template.

To resolve this issue, review the parameters in your [message template](https://www.facebook.com/business/help/2055875911147364?id=2129163877102343). Pay attention to each parameter's data type and the order they're defined in the template.

Check the data that n8n is mapping to the template parameters. If you're using expressions to set parameter values, check the input data to make sure each item resolves to a valid value. You may want to use the [Edit Fields (Set) node](https://docs.n8n.io/integrations/builtin/core-nodes/n8n-nodes-base.set) or set a fallback value to ensure you send a value with the correct format.

### Working with non-text media

The WhatsApp Business Cloud node can work with non-text messages and media like images, audio, documents, and more.

If your operation includes a **Input Data Field Name** or **Property Name** parameter, set this to the field name itself rather than referencing the data in an expression.

For example, if you are trying to send a message with an "Image" **MessageType** and **Take Image From** set to "n8n", set **Input Data Field Name** to a field name like `data` instead of an expression like `{{ $json.input.data }}`.
