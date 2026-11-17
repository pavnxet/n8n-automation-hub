<!-- n8n built-in node reference: n8n-nodes-base.s3 | source: https://docs.n8n.io/integrations/builtin/app-nodes/n8n-nodes-base.s3 -->

Use the S3 node to automate work in non-AWS S3 storage and integrate S3 with other applications. n8n has built-in support for a wide range of S3 features, including creating, deleting, and getting buckets, files, and folders. For AWS S3, use [AWS S3](https://docs.n8n.io/integrations/builtin/app-nodes/n8n-nodes-base.awss3).

Use the S3 node for non-AWS S3 solutions like:

* [MinIO](https://min.io/)
* [Wasabi](https://wasabi.com/)
* [Digital Ocean spaces](https://www.digitalocean.com/products/spaces)

On this page, you'll find a list of operations the S3 node supports and links to more resources.

> **Credentials:**
> Refer to [S3 credentials](https://docs.n8n.io/integrations/builtin/credentials/s3) for guidance on setting up authentication.

> **AI tool:** This node can be used as an AI tool. Connect it to the Tools input of an AI Agent node so the agent can call it.

## Operations

* Bucket
  * Create a bucket
  * Delete a bucket
  * Get all buckets
  * Search within a bucket
*   File

    * Copy a file
    * Delete a file
    * Download a file
    * Get all files
    * Upload a file

    
> **Note:** Attach file for upload To attach a file for upload, use another node to pass the file as a data property. Nodes like the Read/Write Files from Disk node or the HTTP Request work well.

* Folder
  * Create a folder
  * Delete a folder
  * Get all folders

## Templates and examples

[Browse S3 node documentation integration templates](https://n8n.io/integrations/s3) or [search all templates](https://n8n.io/workflows/)

## Node reference

### Setting file permissions in Wasabi

When uploading files to [Wasabi](https://wasabi.com/), you must set permissions for the files using the **ACL** dropdown and not the toggles.

![File permissions when using the S3 node with Wasabi](https://docs.n8n.io/integrations/.gitbook/assets/acl_dropdown.png)
