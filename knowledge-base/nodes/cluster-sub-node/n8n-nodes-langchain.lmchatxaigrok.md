<!-- n8n built-in node reference: n8n-nodes-langchain.lmchatxaigrok | source: https://docs.n8n.io/integrations/builtin/cluster-nodes/sub-nodes/n8n-nodes-langchain.lmchatxaigrok -->

Use the xAI Grok Chat Model node to access xAI Grok's large language models for conversational AI and text generation tasks.

On this page, you'll find the node parameters for the xAI Grok Chat Model node, and links to more resources.

> **Credentials:**
> Refer to the [xAI credentials documentation](https://docs.n8n.io/integrations/builtin/credentials/xai) for authentication information for this node.

## Node parameters

* **Model**: Select the model which will generate the completion. n8n dynamically loads available models from the xAI Grok API. Learn more in the [xAI Grok model documentation](https://docs.x.ai/docs/models).

## Node options

* **Frequency Penalty**: Use this option to control the chances of the model repeating itself. Higher values reduce the chance of the model repeating itself.
* **Maximum Number of Tokens**: Enter the maximum number of tokens used, which sets the completion length. Most models have a context length of 2048 tokens with the newest models supporting up to 32,768 tokens. 
* **Response Format**: Choose **Text** or **JSON**. **JSON** ensures the model returns valid JSON.
* **Presence Penalty**: Use this option to control the chances of the model talking about new topics. Higher values increase the chance of the model talking about new topics.
* **Sampling Temperature**: Use this option to control the randomness of the sampling process. A higher temperature creates more diverse sampling, but increases the risk of hallucinations.
* **Timeout**: Enter the maximum request time in milliseconds.
* **Max Retries**: Enter the maximum number of times to retry a request.
* **Top P**: Use this option to set the probability the completion should use. Use a lower value to ignore less probable options. 

## Templates and examples

[Browse xAI Grok Chat Model node documentation integration templates](https://n8n.io/integrations/xai-grok-chat-model) or [search all templates](https://n8n.io/workflows/)

## Related resources

Refer to [xAI Grok's API documentation](https://docs.x.ai/docs/api-reference) for more information about the service.
