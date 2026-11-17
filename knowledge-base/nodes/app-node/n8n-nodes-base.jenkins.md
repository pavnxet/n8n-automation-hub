<!-- n8n built-in node reference: n8n-nodes-base.jenkins | source: https://docs.n8n.io/integrations/builtin/app-nodes/n8n-nodes-base.jenkins -->

Use the Jenkins node to automate work in Jenkins, and integrate Jenkins with other applications. n8n has built-in support for a wide range of Jenkins features, including listing builds, managing instances, and creating and copying jobs. 

On this page, you'll find a list of operations the Jenkins node supports and links to more resources.

> **Credentials:**
> Refer to [Jenkins credentials](https://docs.n8n.io/integrations/builtin/credentials/jenkins) for guidance on setting up authentication.

> **AI tool:** This node can be used as an AI tool. Connect it to the Tools input of an AI Agent node so the agent can call it.

## Operations

* Build
    * List Builds
* Instance
    * Cancel quiet down state
    * Put Jenkins in quiet mode, no builds can be started, Jenkins is ready for shutdown
    * Restart Jenkins immediately on environments where it's possible
    * Restart Jenkins once no jobs are running on environments where it's possible
    * Shutdown once no jobs are running
    * Shutdown Jenkins immediately
* Job
    * Copy a specific job
    * Create a new job
    * Trigger a specific job
    * Trigger a specific job

## Templates and examples

[Browse Jenkins node documentation integration templates](https://n8n.io/integrations/jenkins) or [search all templates](https://n8n.io/workflows/)
