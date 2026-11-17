<!-- n8n built-in node reference: n8n-nodes-langchain.lmopenhuggingfaceinference | source: https://docs.n8n.io/integrations/builtin/cluster-nodes/sub-nodes/n8n-nodes-langchain.lmopenhuggingfaceinference -->

Use the Hugging Face Inference Model node to use Hugging Face's models.

On this page, you'll find the node parameters for the Hugging Face Inference Model node, and links to more resources.

This node lacks tools support, so it won't work with the [AI Agent](https://docs.n8n.io/integrations/builtin/cluster-nodes/root-nodes/n8n-nodes-langchain.agent) node. Instead, connect it with the [Basic LLM Chain](https://docs.n8n.io/integrations/builtin/cluster-nodes/root-nodes/n8n-nodes-langchain.chainllm) node.

> **Credentials:**
> Refer to the [Hugging Face credentials documentation](https://docs.n8n.io/integrations/builtin/credentials/huggingface) for authentication information for this node.

## Node parameters

* **Model**: Select the model to use to generate the completion.

## Node options

* **Custom Inference Endpoint**: Enter a custom inference endpoint URL.
* **Frequency Penalty**: Use this option to control the chances of the model repeating itself. Higher values reduce the chance of the model repeating itself.
* **Maximum Number of Tokens**: Enter the maximum number of tokens used, which sets the completion length.
* **Presence Penalty**: Use this option to control the chances of the model talking about new topics. Higher values increase the chance of the model talking about new topics.
* **Sampling Temperature**: Use this option to control the randomness of the sampling process. A higher temperature creates more diverse sampling, but increases the risk of hallucinations.
* **Top K**: Enter the number of token choices the model uses to generate the next token.
* **Top P**: Use this option to set the probability the completion should use. Use a lower value to ignore less probable options.

## Templates and examples

[Browse Hugging Face Inference Model node documentation integration templates](https://n8n.io/integrations/hugging-face-inference-model) or [search all templates](https://n8n.io/workflows/)

## Related resources
