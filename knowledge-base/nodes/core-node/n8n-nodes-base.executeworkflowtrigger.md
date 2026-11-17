<!-- n8n built-in node reference: n8n-nodes-base.executeworkflowtrigger | source: https://docs.n8n.io/integrations/builtin/core-nodes/n8n-nodes-base.executeworkflowtrigger -->

Use this node to start a workflow in response to another workflow. It should be the first node in the workflow.

n8n allows you to call workflows from other workflows. This is useful if you want to:

* Reuse a workflow: for example, you could have multiple workflows pulling and processing data from different sources, then have all those workflows call a single workflow that generates a report.
* Break large workflows into smaller components.

## Usage

This node runs in response to a call from the [Execute Sub-workflow](https://docs.n8n.io/integrations/builtin/core-nodes/n8n-nodes-base.executeworkflow) or [Call n8n Workflow Tool](https://docs.n8n.io/integrations/builtin/cluster-nodes/sub-nodes/n8n-nodes-langchain.toolworkflow) nodes.

## Templates and examples

[Browse Execute Sub-workflow Trigger node documentation integration templates](https://n8n.io/integrations/execute-workflow-trigger) or [search all templates](https://n8n.io/workflows/)

## How data passes between workflows
