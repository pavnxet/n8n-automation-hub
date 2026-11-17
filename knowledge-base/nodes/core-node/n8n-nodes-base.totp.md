<!-- n8n built-in node reference: n8n-nodes-base.totp | source: https://docs.n8n.io/integrations/builtin/core-nodes/n8n-nodes-base.totp -->

The TOTP node provides a way to generate a TOTP (time-based one-time password).

> **Credentials:**
> Refer to [TOTP credentials](https://docs.n8n.io/integrations/builtin/credentials/totp) for guidance on setting up authentication.

## Node parameters

> **AI tool:** This node can be used as an AI tool. Connect it to the Tools input of an AI Agent node so the agent can call it.

Configure this node with these parameters.

### Credential to connect with

Select or create a [TOTP credential](https://docs.n8n.io/integrations/builtin/credentials/totp) for the node to use.

### Operation

**Generate Secret** is the only operation currently supported.

## Node options

Use these **Options** to further configure the node.

### Algorithm

Select the HMAC hashing algorithm to use. Default is SHA1.

### Digits

Enter the number of digits in the generated code. Default is `6`.

### Period

Enter how many seconds the TOTP is valid for. Default is `30`.

## Templates and examples

[Browse TOTP integration templates](https://n8n.io/integrations/totp) or [search all templates](https://n8n.io/workflows/)
