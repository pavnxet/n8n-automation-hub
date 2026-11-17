<!-- n8n built-in node reference: n8n-nodes-base.executecommand | source: https://docs.n8n.io/integrations/builtin/core-nodes/n8n-nodes-base.executecommand -->

The Execute Command node runs shell commands on the host machine that runs n8n.

> **Security considerations:**
> The Execute Command node can introduce significant security risks in environments that operate with untrusted users. Because of this, the node is [disabled](https://app.gitbook.com/s/jm0ZYRpZIPWge2ZSiDYO/host-n8n/configure-n8n/security/block-specific-nodes#exclude-nodes) by default from n8n 2.0.

> **Which shell runs the command?:**
> This node executes the command in the default shell of the host machine. For example, `cmd` on Windows and `zsh` on macOS.
> If you run n8n with Docker, your command will run in the n8n container and not the Docker host.
> If you're using [queue mode](https://app.gitbook.com/s/jm0ZYRpZIPWge2ZSiDYO/host-n8n/configure-n8n/scaling/enable-queue-mode), the command runs on the worker that's executing the task in production mode. When running manual executions, it runs on the main instance, unless you set `OFFLOAD_MANUAL_EXECUTIONS_TO_WORKERS` to `true`.

> **Feature availability:**
> The Execute Command node is available on:
> - **Self-hosted:** All editions
> It isn't available on n8n Cloud.

## Node parameters

Configure the node using the following parameters.

### Execute Once

Choose whether you want the node to execute only once (turned on) or once for every item it receives as input (turned off).

### Command

Enter the command to execute on the host machine. Refer to sections below for examples of running [multiple commands](https://docs.n8n.io/integrations/builtin/core-nodes/n8n-nodes-base.executecommand#run-multiple-commands) and [cURL commands](https://docs.n8n.io/integrations/builtin/core-nodes/n8n-nodes-base.executecommand#run-curl-command).

#### Run multiple commands

Use one of two methods to run multiple commands in one Execute Command node:

*   Enter each command on one line separated by `&&`. For example, you can combine the change directory (cd) command with the list (ls) command using `&&`.

    ```bash
    cd bin && ls
    ```
*   Enter each command on a separate line. For example, you can write the list (ls) command on a new line after the change directory (cd) command.

    ```bash
    cd bin
    ls
    ```

#### Run cURL command

You can also use the [HTTP Request](https://docs.n8n.io/integrations/builtin/core-nodes/n8n-nodes-base.httprequest) node to make a cURL request.

If you want to run the curl command in the Execute Command node, you will have to build a Docker image based on the existing n8n image. The default n8n Docker image uses Alpine Linux.

> **`apk` isn't included in the n8n image:**
> The `apk` package manager was removed from the official n8n Docker image. To install a package like `curl`, you need to restore `apk` from a fresh Alpine base image first, as shown below.

1. Create a file named `Dockerfile`.
2. Add the below code snippet to the Dockerfile.

```shell
   FROM n8nio/n8n
   USER root

   # Restore the apk package manager (removed from the base image)
   COPY --from=alpine:3.22 /sbin/apk /sbin/apk
   COPY --from=alpine:3.22 /lib/apk /lib/apk
   COPY --from=alpine:3.22 /usr/lib/libapk* /usr/lib/

   RUN apk add --no-cache curl
   USER node
```
3. In the same folder, execute the command below to build the Docker image.

```shell
   docker build -t n8n-curl .
```
4. Replace the Docker image you used before. For example, replace `n8nio/n8n` with `n8n-curl`.
5. Run the newly created Docker image. You'll now be able to execute curl using the Execute Command Node.

## Templates and examples

[Browse n8n-nodes-base.executecommand integration templates](https://n8n.io/integrations/execute-command) or [search all templates](https://n8n.io/workflows/)

## Common issues

For common questions or issues and suggested solutions, refer to [Common Issues](https://docs.n8n.io/integrations/builtin/core-nodes/n8n-nodes-base.executecommand/common-issues).

---

## Execute Command node common issues

## Execute Command node common issues

Here are some common errors and issues with the [Execute Command node](https://docs.n8n.io/integrations/builtin/core-nodes/n8n-nodes-base.executecommand) and steps to resolve or troubleshoot them.

### Command failed: &lt;command&gt; /bin/sh: &lt;command&gt;: not found

This error occurs when the shell environment can't find one of the commands in the **Command** parameter.

To fix this error, review the following:

* Check that the command and its arguments don't have typos in the **Command** parameter.
* Check that the command is in the `PATH` of the user running n8n. 
* If you are running n8n with Docker, check if the command is available within the container by trying to run it manually. If your command isn't included in the container, you might have to extend the official n8n image with a [custom image](https://docs.docker.com/build/building/base-images/) that includes your command.
	* If n8n is already running:
		```sh
		# Find n8n's container ID, it will be the first column
		docker ps | grep n8n
		# Try to execute the command within the running container
		docker container exec <container_ID> <command_to_run>
		```
	* If n8n isn't running:
		```sh
		# Start up a new container that runs the command instead of n8n
		# Use the same image and tag that you use to run n8n normally
		docker run -it --rm --entrypoint /bin/sh n8nio/n8n -c <command_to_run>
		```

### Error: stdout maxBuffer length exceeded

This error happens when your command returns more output than the Execute Command node is able to process at one time.

To avoid this error, reduce output your command produces. Check your command's manual page or documentation to see if there are flags to limit or filter output. If not, you may need to pipe the output to another command to remove unneeded info.

### PowerShell commands get truncated at line breaks

On Windows, the Execute Command node passes the **Command** parameter to the system shell as a single string. If your command contains line breaks, the shell only executes the first line and ignores the rest.

This is a Windows shell limitation. The underlying `cmd.exe` process treats each line break as the end of the command.

To fix this, write your PowerShell command on a single line. If the command is complex, join statements with semicolons:

```powershell
powershell -Command "Get-ChildItem C:\Data; Write-Output 'Done'"
```

For longer scripts, save the script to a file and run it with the `-File` flag instead:

```powershell
powershell -File C:\Scripts\my-script.ps1
```
