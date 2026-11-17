<!-- n8n built-in node reference: n8n-nodes-base.gitlab | source: https://docs.n8n.io/integrations/builtin/app-nodes/n8n-nodes-base.gitlab -->

Use the GitLab node to automate work in GitLab, and integrate GitLab with other applications. n8n has built-in support for a wide range of GitLab features, including creating, updating, deleting, and editing issues, repositories, releases and users. 

On this page, you'll find a list of operations the GitLab node supports and links to more resources.

> **Credentials:**
> Refer to [GitLab credentials](https://docs.n8n.io/integrations/builtin/credentials/gitlab) for guidance on setting up authentication.

> **AI tool:** This node can be used as an AI tool. Connect it to the Tools input of an AI Agent node so the agent can call it.

## Operations

* File
	* Create
	* Delete
	* Edit
	* Get
	* List
* Issue
    * Create a new issue
    * Create a new comment on an issue
    * Edit an issue
    * Get the data of a single issue
    * Lock an issue
* Release
    * Create a new release
    * Delete a new release
    * Get a new release
    * Get all releases
    * Update a new release
* Repository
    * Get the data of a single repository
    * Returns issues of a repository
* User
    * Returns the repositories of a user

## Working with subgroups and nested repositories

If your repository is located within nested GitLab groups or subgroups (for example, `https://gitlab.com/org/subgroup1/subgroup2/my-repo`), GitLab's API requires you to URL-encode the namespace path.

To configure the node for nested subgroups:

1. **Project Owner**: Enter the full subgroup hierarchy up to the repository, replacing all forward slashes (`/`) with `%2F`. Example: `org%2Fsubgroup1%2Fsubgroup2`
2. **Project Name**: Enter the project's repository slug. Example: `my-repo`

## Templates and examples

[Browse GitLab node documentation integration templates](https://n8n.io/integrations/gitlab) or [search all templates](https://n8n.io/workflows/)

## Related resources

Refer to [GitLab's documentation](https://docs.gitlab.com/ee/api/rest/) for more information about the service.

n8n provides a trigger node for GitLab. Refer to the [GitLab Trigger node documentation](https://docs.n8n.io/integrations/builtin/trigger-nodes/n8n-nodes-base.gitlabtrigger) for more information.
