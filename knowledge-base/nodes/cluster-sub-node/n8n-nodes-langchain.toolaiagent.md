<!-- n8n built-in node reference: n8n-nodes-langchain.toolaiagent | source: https://docs.n8n.io/integrations/builtin/cluster-nodes/sub-nodes/n8n-nodes-langchain.toolaiagent -->

The AI Agent Tool node allows a root-level agent[^1] in your workflow to call other agents as tools to simplify multi-agent orchestration.

The [primary agent](https://docs.n8n.io/integrations/builtin/cluster-nodes/root-nodes/n8n-nodes-langchain.agent/tools-agent) can supervise and delegate work to AI Agent Tool nodes that specialize in different tasks and knowledge. This allows you to use multiple agents in a single workflow without the complexity of managing context and variables that sub-workflows require. You can nest AI Agent Tool nodes into multiple layers for more complex multi-tiered use cases.

On this page, you'll find the node parameters for the AI Agent Tool node, and links to more resources.

## Node parameters

Configure the AI Agent Tool node using these parameters:

* **Description**: Give a description to the LLM of this agent's purpose and scope of responsibility. A good, specific description tells the parent agent when to delegate tasks to this agent for processing.
* **Prompt (User Message)**: The prompt to the LLM explaining what actions to perform and what information to return.
* **Require Specific Output Format**: Whether you want the node to require a specific output format. When turned on, n8n prompts you to connect one of the output parsers [described on the main agent page](https://docs.n8n.io/integrations/builtin/cluster-nodes/root-nodes/n8n-nodes-langchain.agent/tools-agent#require-specific-output-format).
* **Enable Fallback Model**: Whether to enable a fallback model. When enabled, n8n prompts you to connect a backup chat model to use in case the primary model fails or isn't available.

## Node options

Refine the AI Agent Tool node's behavior using these options:

* **System Message**: A message to send to the agent before the conversation starts.
* **Max Iterations**: The maximum number of times the model should run to generate a response before stopping.
* **Return Intermediate Steps**: Whether to include intermediate steps the agent took in the final output.
* **Automatically Passthrough Binary Images**: Whether binary images should be automatically passed through to the agent as image type messages.
* **Batch Processing**: Whether to enable the following batch processing options for rate limiting:
	* **Batch Size**: The number of items to process in parallel. This helps with rate limiting but may impact the log output ordering.
	* **Delay Between Batches**: The number of milliseconds to wait between batches.

## Templates and examples

[Browse AI Agent Tool node documentation integration templates](https://n8n.io/integrations/ai-agent-tool) or [search all templates](https://n8n.io/workflows/)

## Dynamic parameters for tools with `$fromAI()`

To learn how to dynamically populate parameters for app node tools, refer to [Let AI specify tool parameters with `$fromAI()`](https://app.gitbook.com/s/rPN1zU5jaYNvwH7RzxqA/integrate-ai/ai-examples/use-ai-for-parameters).

[^1]: AI agents are artificial intelligence systems capable of responding to requests, making decisions, and performing real-world tasks for users. They use large language models (LLMs) to interpret user input and make decisions about how to best process requests using the information and resources they have available.
