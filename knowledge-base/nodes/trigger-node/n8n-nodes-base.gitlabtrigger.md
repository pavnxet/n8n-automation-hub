<!-- n8n built-in node reference: n8n-nodes-base.gitlabtrigger | source: https://docs.n8n.io/integrations/builtin/trigger-nodes/n8n-nodes-base.gitlabtrigger -->

[GitLab](https://gitlab.com/) is a web-based DevOps lifecycle tool that provides a Git-repository manager providing wiki, issue-tracking, and continuous integration/continuous installation pipeline features.

> **Credentials:**
> Refer to the [GitLab credentials documentation](https://docs.n8n.io/integrations/builtin/credentials/gitlab) for authentication information for this node.

> **Examples and templates:**
> For usage examples and templates to help you get started, refer to n8n's [GitLab Trigger integrations](https://n8n.io/integrations/gitlab-trigger/) page.

## Events

* Comment
* Confidential issues
* Confidential comments
* Deployments
* Issue
* Job
* Merge request
* Pipeline
* Push
* Release
* Tag
* Wiki page

## Working with subgroups and nested repositories

If your repository is located within nested GitLab groups or subgroups (for example, `https://gitlab.com/org/subgroup1/subgroup2/my-repo`), GitLab's API requires you to URL-encode the namespace path.

To configure the node for nested subgroups:

1. **Repository Owner**: Enter the full subgroup hierarchy up to the repository, replacing all forward slashes (`/`) with `%2F`. Example: `org%2Fsubgroup1%2Fsubgroup2`
2. **Repository Name**: Enter the project's repository slug. Example: `my-repo`

## Related resources

n8n provides an app node for GitLab. Refer to the [GitLab node documentation](https://docs.n8n.io/integrations/builtin/app-nodes/n8n-nodes-base.gitlab) for more information.

View [example workflows and related content](https://n8n.io/integrations/gitlab-trigger/) on n8n's website.

Refer to [GitLab's documentation](https://docs.gitlab.com/api/rest/) for details about their API.
