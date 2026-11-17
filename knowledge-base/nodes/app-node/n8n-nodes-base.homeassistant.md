<!-- n8n built-in node reference: n8n-nodes-base.homeassistant | source: https://docs.n8n.io/integrations/builtin/app-nodes/n8n-nodes-base.homeassistant -->

Use the Home Assistant node to automate work in Home Assistant, and integrate Home Assistant with other applications. n8n has built-in support for a wide range of Home Assistant features, including getting, creating, and checking camera proxies, configurations, logs, services, and templates. 

On this page, you'll find a list of operations the Home Assistant node supports and links to more resources.

> **Credentials:**
> Refer to [Home Assistant credentials](https://docs.n8n.io/integrations/builtin/credentials/homeassistant) for guidance on setting up authentication.

> **AI tool:** This node can be used as an AI tool. Connect it to the Tools input of an AI Agent node so the agent can call it.

## Operations

* Camera Proxy
    * Get the camera screenshot
* Config
    * Get the configuration
    * Check the configuration
* Event
    * Create an event
    * Get all events
* Log
    * Get a log for a specific entity
    * Get all logs
* Service
    * Call a service within a specific domain
    * Get all services
* State
    * Create a new record, or update the current one if it already exists (upsert)
    * Get a state for a specific entity
    * Get all states
* Template
    * Create a template

## Templates and examples

[Browse Home Assistant node documentation integration templates](https://n8n.io/integrations/home-assistant) or [search all templates](https://n8n.io/workflows/)

## Related resources

Refer to [Home Assistant's documentation](https://developers.home-assistant.io/docs/api/rest/) for more information about the service.
