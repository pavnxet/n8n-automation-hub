<!-- n8n built-in node reference: n8n-nodes-langchain.lmchatopenai | source: https://docs.n8n.io/integrations/builtin/cluster-nodes/sub-nodes/n8n-nodes-langchain.lmchatopenai -->

> **Note:** On n8n Cloud, you can use the OpenAI Chat Model node with [Gateway credits](https://app.gitbook.com/s/jm0ZYRpZIPWge2ZSiDYO/use-n8n-cloud/gateway-credits) instead of your own OpenAI API key. Select **Use Gateway credits** in the node's credential field to run the node without an OpenAI account.

Use the OpenAI Chat Model node to use OpenAI's chat models with conversational agents[^1].

On this page, you'll find the node parameters for the OpenAI Chat Model node and links to more resources.

> **Credentials:**
> Refer to the [OpenAI credentials documentation](https://docs.n8n.io/integrations/builtin/credentials/openai) for authentication information for this node.

## Node parameters

### Model

Select the model to use to generate the completion.

n8n dynamically loads models from OpenAI, and you'll only see the models available to your account.

### Use Responses API

OpenAI provides two endpoints for generating output from a model:

* **Chat Completions**: The Chat Completions API endpoint generates a model response from a list of messages that comprise a conversation. The API requires the user to handle conversation state manually, for example by adding a [Simple Memory](https://docs.n8n.io/integrations/builtin/cluster-nodes/sub-nodes/n8n-nodes-langchain.memorybufferwindow) subnode. For new projects, OpenAI recommends to use the Responses API.
* **Responses**: The Responses API is an agentic loop, allowing the model to call multiple built-in tools within the span of one API request. It also supports persistent conversations by passing a `conversation_id`.

Toggle to **Use Responses API** if you want the model to generate output using the Responses API. Otherwise, the OpenAI Chat Model node will default to using the Chat Completions API.

Refer to the OpenAI documentation for a [comparison of the Chat Completions and Responses APIs](https://platform.openai.com/docs/guides/migrate-to-responses).

### Built-in Tools

The OpenAI Responses API provides a range of [built-in tools](https://platform.openai.com/docs/guides/tools) to enrich the model's response. Toggle to **Use Responses API** if you want the model to have access to the following built-in tools:

* **Web Search**: Allows models to search the web for the latest information before generating a response.
* **File Search**: Allow models to search your knowledgebase from previously uploaded files for relevant information before generating a response. Refer to the [OpenAI documentation](https://platform.openai.com/docs/guides/tools-file-search) for more information.
* **Code Interpreter**: Allows models to write and run Python code in a sandboxed environment.

> **Use with AI Agent node:**
> Built-in tools are only supported when using the OpenAI Chat Model node in combination with the AI Agent node. Built-in tools aren't available when using the OpenAI Chat Model node in combination with a Basic LLM Chain node, for example.

## Node options

Use these options to further refine the node's behavior. The following options are available whether you use the Responses API to generate model output or not.

### Frequency Penalty

Use this option to control the chances of the model repeating itself. Higher values reduce the chance of the model repeating itself.

### Maximum Number of Tokens

Enter the maximum number of tokens used, which sets the completion length.

### Presence Penalty

Use this option to control the chances of the model talking about new topics. Higher values increase the chance of the model talking about new topics.

### Sampling Temperature

Use this option to control the randomness of the sampling process. A higher temperature creates more diverse sampling, but increases the risk of hallucinations.

### Timeout

Enter the maximum request time in milliseconds.

### Max Retries

Enter the maximum number of times to retry a request.

### Top P

Use this option to set the probability the completion should use. Use a lower value to ignore less probable options.

## Additional node options (Responses API only)

The following, additional options are available when toggling to **Use Responses API**.

### Conversation ID

The conversation that this response belongs to. Input items and output items from this response are automatically added to this conversation after this response completes.

### Prompt Cache Key

Use this key for caching similar requests to optimize cache hit rates.

### Safety Identifier

Apply an identifier to track users who may violate usage policies.

### Service Tier

Select the service tier that fits your needs: Auto, Flex, Default, or Priority.

### Metadata

A set of key-value pairs for storing structured information. You can attach up to 16 pairs to an object, which is useful for adding custom data that can be used for searching by the API or in the dashboard.

### Top Logprobs

Define an integer between 0 and 20 specifying the number of most likely tokens to return at each token position, each with an associated log probability.

### Output Format

Choose a response format: Text, JSON Schema, or JSON Object. Use of JSON Schema is recommended, if you want to receive data in JSON format.

### Prompt

Configure the prompt filled with a unique ID, its version, and substitutable variables. Prompts are configured through the OpenAI dashboard.

## Templates and examples

[Browse n8n-nodes-langchain.lmchatopenai integration templates](https://n8n.io/integrations/openai-chat-model) or [search all templates](https://n8n.io/workflows/)

## Related resources

Refer to [LangChain's OpenAI documentation](https://docs.langchain.com/oss/javascript/integrations/chat/openai) for more information about the service.

Refer to [OpenAI documentation](https://platform.openai.com/docs/api-reference/responses/create) for more information about the parameters.

## Common issues

For common questions or issues and suggested solutions, refer to [Common issues](https://docs.n8n.io/integrations/builtin/cluster-nodes/sub-nodes/n8n-nodes-langchain.lmchatopenai/common-issues).

[^1]: AI agents are artificial intelligence systems capable of responding to requests, making decisions, and performing real-world tasks for users. They use large language models (LLMs) to interpret user input and make decisions about how to best process requests using the information and resources they have available.

---

## OpenAI Chat Model node common issues

## OpenAI Chat Model node common issues

Here are some common errors and issues with the [OpenAI Chat Model node](https://docs.n8n.io/integrations/builtin/cluster-nodes/sub-nodes/n8n-nodes-langchain.lmchatopenai) and steps to resolve or troubleshoot them.

### Processing parameters

The OpenAI Chat Model node is a sub-node[^1]. Sub-nodes behave differently than other nodes when processing multiple items using expressions.

Most nodes, including [root nodes](#user-content-fn-2)[^2], take any number of items as input, process these items, and output the results. You can use expressions to refer to input items, and the node resolves the expression for each item in turn. For example, given an input of five name values, the expression `{{ $json.name }}` resolves to each name in turn.

In sub-nodes, the expression always resolves to the first item. For example, given an input of five name values, the expression `{{ $json.name }}` always resolves to the first name.

[^1]: n8n cluster nodes consist of one or more sub-nodes connected to a root node. Sub-nodes extend the functionality of the root node, providing access to specific services or resources or offering specific types of dedicated processing, like calculator functionality, for example.
[^2]: Each n8n cluster node contains a single root node that defines the main functionality of the cluster. One or more sub-nodes attach to the root node to extend its functionality.
