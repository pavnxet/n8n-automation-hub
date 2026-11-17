<!-- n8n built-in node reference: n8n-nodes-base.code | source: https://docs.n8n.io/integrations/builtin/core-nodes/n8n-nodes-base.code -->

The Code node lets you run your own JavaScript or Python inside a workflow, so you can transform data or add logic the built-in nodes don't cover.

## Common issues

For common questions or issues and suggested solutions, refer to [Common Issues](https://docs.n8n.io/integrations/builtin/core-nodes/n8n-nodes-base.code/common-issues).

---

## Code node common issues

## Common issues

Here are some common errors and issues with the [Code node](https://docs.n8n.io/integrations/builtin/core-nodes/n8n-nodes-base.code) and steps to resolve or troubleshoot them.

### Code doesn't return items properly

This error occurs when the code in your Code node doesn't return data in the expected format.

In n8n, all data passed between nodes is an array of objects. Each of these objects wraps another object with the `json` key:

```javascript
[
  {
    "json": {
	  // your data goes here
	}
  }
]
```

To troubleshoot this error, check the following:

* Read the [data structure](https://app.gitbook.com/s/rPN1zU5jaYNvwH7RzxqA/work-with-data/understand-n8ns-data-structure) to understand the data you receive in the Code node and the requirements for outputting data from the node.
* Understand how data items work and how to connect data items from previous nodes with [item linking](https://app.gitbook.com/s/rPN1zU5jaYNvwH7RzxqA/work-with-data/reference-data/link-data-items).

### A 'json' property isn't an object

This error occurs when the Code node returns data where the `json` key isn't pointing to an object.

This may happen if you set `json` to a different data structure, like an array:

```javascript
[
  {
    "json": [
	  // Setting `json` to an array like this will produce an error
	]
  }
]
```

To resolve this, ensure that the `json` key references an object in your return data:

```javascript
[
  {
    "json": {
	  // Setting `json` to an object as expected
	}
  }
]
```

### Code doesn't return an object

This error may occur when your Code node doesn't return anything or if it returns an unexpected result.

To resolve this, ensure that your Code node returns the [expected data structure](https://app.gitbook.com/s/rPN1zU5jaYNvwH7RzxqA/work-with-data/understand-n8ns-data-structure):

```javascript
[
  {
    "json": {
	  // your data goes here
	}
  }
]
```

This error may also occur if the code you provided returns `'undefined'` instead of the expected result. In that case, ensure that the data you are referencing in your Code node exists in each execution and that it has the structure your code expects.

### 'import' and 'export' may only appear at the top level

This error occurs if you try to use `import` or `export` in the Code node. These aren't supported by n8n's JavaScript sandbox. Instead, use the `require` function to load modules.

To resolve this issue, try changing your `import` statements to use `require`:

```javascript
// Original code:
// import express from "express";
// New code:
const express = require("express");
```

### Cannot find module '\<module>'

This error occurs if you try to use `require` in the Code node and n8n can't find the module.

> **Only for self-hosted:**
> n8n doesn't support importing modules in the [Cloud](https://app.gitbook.com/s/jm0ZYRpZIPWge2ZSiDYO/use-n8n-cloud) version.

If you're [self-hosting](https://app.gitbook.com/s/jm0ZYRpZIPWge2ZSiDYO/host-n8n) n8n, follow these steps:

* Install the module into your n8n environment.
  * If you are running n8n with [npm](https://app.gitbook.com/s/jm0ZYRpZIPWge2ZSiDYO/host-n8n/install-options/install-with-npm), install the module in the same environment as n8n.
  * If you are running n8n with [Docker](https://app.gitbook.com/s/jm0ZYRpZIPWge2ZSiDYO/host-n8n/install-options/install-with-docker), you need to extend the official n8n image with a [custom image](https://docs.docker.com/build/building/base-images/) that includes your module.
* Set the `NODE_FUNCTION_ALLOW_BUILTIN` and `NODE_FUNCTION_ALLOW_EXTERNAL` [environment variables](https://app.gitbook.com/s/jm0ZYRpZIPWge2ZSiDYO/host-n8n/configure-n8n/basic-configuration/configuration-examples/enable-modules-in-code-node) to allow importing modules.

### Using global variables

Sometimes you may wish to set and retrieve simple global data related to a workflow across and within executions. For example, you may wish to include the date of the previous report when compiling a report with a list of project updates.

To set, update, and retrieve data directly to a workflow, use the [static data](https://app.gitbook.com/s/rPN1zU5jaYNvwH7RzxqA/code-in-n8n/cookbook/built-in-methods-and-variables-examples/getworkflowstaticdata) functions within your code. You can manage data either globally or tied to specific nodes.

> **Use Remove Duplicates when possible:**
> If you're interested in using variables to avoid processing the same data items more than once, consider using the [Remove Duplicates node](https://docs.n8n.io/integrations/builtin/core-nodes/n8n-nodes-base.removeduplicates) instead. The Remove Duplicates node can save information across executions to avoid processing the same items multiple times.

### Can't access credentials in a code node

By design, Code nodes can't access credentials. They don't have access to n8n’s internal credential management system. This prevents exposure of sensitive authentication data.

Attempts to reference credentials in a Code node using expressions or methods like `this.getCredentials()` or `$getCredentials()` will result in errors, such as `this.getCredentials is not a function` and `$getCredentials is not defined`.

If you need to make authenticated API calls, use the [HTTP Request node](https://docs.n8n.io/integrations/builtin/core-nodes/n8n-nodes-base.httprequest) which provides credential support.

To work with credentials dynamically, handle the credential selection logic outside of the Code node:

* Use a [Switch](https://docs.n8n.io/integrations/builtin/core-nodes/n8n-nodes-base.switch) node to route to different nodes with different credentials.
* Use expressions directly in credential fields to select credentials dynamically based on previous node data.
* Use an HTTP Request node with Custom Auth to dynamically set headers, query parameters, or body values using expressions.

---

## Code editor keyboard shortcuts

## Keyboard shortcuts when using the Code editor

The Code node editing environment supports a range of keyboard shortcuts to speed up and enhance your experience. Select the appropriate tab to see the relevant shortcuts for your operating system.

### Cursor Movement

**Windows**

ActionShortcutMove cursor left<kbd>← Left</kbd>Move cursor right<kbd>→ Right</kbd>Move cursor up<kbd>↑ Up</kbd>Move cursor down<kbd>↓ Down</kbd>Move cursor by word left<kbd>^ Ctrl</kbd> + <kbd>← Left</kbd>Move cursor by word right<kbd>^ Ctrl</kbd> + <kbd>→ Right</kbd>Move to line start<kbd>⤒ Home</kbd> **or** <kbd>^ Ctrl</kbd> + <kbd>← Left</kbd>Move to line end<kbd>⤓ End</kbd> **or** <kbd>^ Ctrl</kbd> + <kbd>→ Right</kbd>Move to document start<kbd>^ Ctrl</kbd> **or** <kbd>⤒ Home</kbd> Move to document end<kbd>^ Ctrl</kbd> **or**  <kbd>⤓ End</kbd> Move page up<kbd>⇞ Page Up</kbd>Move page down<kbd>⇟ Page Down</kbd>

**macOS**

| Action                    | Shortcut                                                                       |
| ------------------------- | ------------------------------------------------------------------------------ |
| Move cursor left          | <kbd>← Left</kbd> **or** <kbd>^ Ctrl</kbd> + <kbd>B</kbd>                      |
| Move cursor right         | <kbd>→ Right</kbd> **or** <kbd>^ Ctrl</kbd> + <kbd>F</kbd>                     |
| Move cursor up            | <kbd>↑ Up</kbd>  **or** <kbd>^ Ctrl</kbd> + <kbd>P</kbd>                       |
| Move cursor down          | <kbd>↓ Down</kbd> **or** <kbd>^ Ctrl</kbd> + <kbd>N</kbd>                      |
| Move cursor by word left  | <kbd>⌥ Option</kbd> + <kbd>← Left</kbd>                                        |
| Move cursor by word right | <kbd>⌥ Option</kbd> + <kbd>→ Right</kbd>                                       |
| Move to line start        | <kbd>⌘ Cmd</kbd> +  <kbd>← Left</kbd> **or** <kbd>^ Ctrl</kbd> + <kbd>A</kbd>  |
| Move to line end          | <kbd>⌘ Cmd</kbd> +  <kbd>→ Right</kbd> **or** <kbd>^ Ctrl</kbd> + <kbd>E</kbd> |
| Move to document start    | <kbd>⌘ Cmd</kbd> + <kbd>↑ Up</kbd>                                             |
| Move to document end      | <kbd>⌘ Cmd</kbd> + <kbd>↓ Down</kbd>                                           |
| Move page up              | <kbd>⇞ Page Up</kbd>                                                           |
| Move page down            | <kbd>⇟ Page Down</kbd>                                                         |

**Linux**

ActionShortcutMove cursor left<kbd>← Left</kbd>Move cursor right<kbd>→ Right</kbd>Move cursor up<kbd>↑ Up</kbd> Move cursor down<kbd>↓ Down</kbd>Move cursor by word left<kbd>^ Ctrl</kbd> + <kbd>← Left</kbd>Move cursor by word right<kbd>^ Ctrl</kbd> + <kbd>→ Right</kbd>Move to line start<kbd>⤒ Home</kbd> **or** <kbd>^ Ctrl</kbd> + <kbd>← Left</kbd>Move to line end<kbd>⤓ End</kbd> **or** <kbd>^ Ctrl</kbd> + <kbd>→ Right</kbd>Move to document start<kbd>^ Ctrl</kbd> **or** <kbd>⤒ Home</kbd> Move to document end<kbd>^ Ctrl</kbd> **or**  <kbd>⤓ End</kbd> Move page up<kbd>⇞ Page Up</kbd>Move page down<kbd>⇟ Page Down</kbd>

### Selection

**Windows**

| Action                          | Shortcut                                               |
| ------------------------------- | ------------------------------------------------------ |
| Selection with any movement key | <kbd>⇧ Shift</kbd> + \[Movement Key]                   |
| Select all                      | <kbd>^ Ctrl</kbd> + <kbd>A</kbd>                       |
| Select line                     | <kbd>^ Ctrl</kbd> + <kbd>L</kbd>                       |
| Select next occurrence          | <kbd>^ Ctrl</kbd> + <kbd>D</kbd>                       |
| Select all occurrences          | <kbd>⇧ Shift</kbd> + <kbd>^ Ctrl</kbd> + <kbd>L</kbd>  |
| Go to matching bracket          | <kbd>⇧ Shift</kbd> + <kbd>^ Ctrl</kbd> + <kbd>\\</kbd> |

**macOS**

| Action                          | Shortcut                                              |
| ------------------------------- | ----------------------------------------------------- |
| Selection with any movement key | <kbd>⇧ Shift</kbd> + \[Movement Key]                  |
| Select all                      | <kbd>⌘ Cmd</kbd> + <kbd>A</kbd>                       |
| Select line                     | <kbd>⌘ Cmd</kbd> + <kbd>L</kbd>                       |
| Select next occurrence          | <kbd>⌘ Cmd</kbd> + <kbd>D</kbd>                       |
| Go to matching bracket          | <kbd>⇧ Shift</kbd> + <kbd>⌘ Cmd</kbd> + <kbd>\\</kbd> |

**Linux**

| Action                          | Shortcut                                               |
| ------------------------------- | ------------------------------------------------------ |
| Selection with any movement key | <kbd>⇧ Shift</kbd> + \[Movement Key]                   |
| Select all                      | <kbd>^ Ctrl</kbd> + <kbd>A</kbd>                       |
| Select line                     | <kbd>^ Ctrl</kbd> + <kbd>L</kbd>                       |
| Select next occurrence          | <kbd>^ Ctrl</kbd> + <kbd>D</kbd>                       |
| Select all occurrences          | <kbd>⇧ Shift</kbd> + <kbd>^ Ctrl</kbd> + <kbd>L</kbd>  |
| Go to matching bracket          | <kbd>⇧ Shift</kbd> + <kbd>^ Ctrl</kbd> + <kbd>\\</kbd> |

### Basic Operations

**Windows**

| Action                    | Shortcut                                                                                      |
| ------------------------- | --------------------------------------------------------------------------------------------- |
| New line with indentation | <kbd>Enter ⏎</kbd>                                                                            |
| Undo                      | <kbd>^ Ctrl</kbd> + <kbd>Z</kbd>                                                              |
| Redo                      | <kbd>^ Ctrl</kbd> + <kbd>Y</kbd> **or** <kbd>^ Ctrl</kbd> + <kbd>⇧ Shift</kbd> + <kbd>V</kbd> |
| Undo selection            | <kbd>^ Ctrl</kbd> + <kbd>U</kbd>                                                              |
| Copy                      | <kbd>^ Ctrl</kbd> + <kbd>C</kbd>                                                              |
| Cut                       | <kbd>^ Ctrl</kbd> + <kbd>X</kbd>                                                              |
| Paste                     | <kbd>^ Ctrl</kbd> + <kbd>V</kbd>                                                              |

**macOS**

| Action                    | Shortcut                                                                                     |
| ------------------------- | -------------------------------------------------------------------------------------------- |
| New line with indentation | <kbd>Enter ⏎</kbd>                                                                           |
| Undo                      | <kbd>⌘ Cmd</kbd> + <kbd>Z</kbd>                                                              |
| Redo                      | <kbd>⌘ Cmd</kbd> + <kbd>Y</kbd> **or** <kbd>⌘ Cmd</kbd> + <kbd>⇧ Shift</kbd> +  <kbd>Y</kbd> |
| Undo selection            | <kbd>⌘ Cmd</kbd> + <kbd>U</kbd>                                                              |
| Copy                      | <kbd>⌘ Cmd</kbd> + <kbd>C</kbd>                                                              |
| Cut                       | <kbd>⌘ Cmd</kbd> + <kbd>X</kbd>                                                              |
| Paste                     | <kbd>⌘ Cmd</kbd> + <kbd>V</kbd>                                                              |

**Linux**

| Action                    | Shortcut                                                                                      |
| ------------------------- | --------------------------------------------------------------------------------------------- |
| New line with indentation | <kbd>Enter ⏎</kbd>                                                                            |
| Undo                      | <kbd>^ Ctrl</kbd> + <kbd>Z</kbd>                                                              |
| Redo                      | <kbd>^ Ctrl</kbd> + <kbd>Y</kbd> **or** <kbd>^ Ctrl</kbd> + <kbd>⇧ Shift</kbd> + <kbd>V</kbd> |
| Undo selection            | <kbd>^ Ctrl</kbd> + <kbd>U</kbd>                                                              |
| Copy                      | <kbd>^ Ctrl</kbd> + <kbd>C</kbd>                                                              |
| Cut                       | <kbd>^ Ctrl</kbd> + <kbd>X</kbd>                                                              |
| Paste                     | <kbd>^ Ctrl</kbd> + <kbd>V</kbd>                                                              |

### Delete Operations

**Windows**

| Action                 | Shortcut                                              |
| ---------------------- | ----------------------------------------------------- |
| Delete character left  | <kbd>⌫ Backspace</kbd>                                |
| Delete character right | <kbd>⌦ Del</kbd>                                      |
| Delete word left       | <kbd>^ Ctrl</kbd> + <kbd>⌫ Backspace</kbd>            |
| Delete word right      | <kbd>^ Ctrl</kbd> + <kbd>⌦ Del</kbd>                  |
| Delete line            | <kbd>⇧ Shift</kbd> + <kbd>^ Ctrl</kbd> + <kbd>K</kbd> |

**macOS**

| Action                 | Shortcut                                                                                                |
| ---------------------- | ------------------------------------------------------------------------------------------------------- |
| Delete character left  | <kbd>⌫ Backspace</kbd>                                                                                  |
| Delete character right | <kbd>⌦ Del</kbd>                                                                                        |
| Delete word left       | <kbd>⌥ Option</kbd> + <kbd>⌫ Backspace</kbd> **or** <kbd>^ Ctrl</kbd> + <kbd>⌘ Cmd</kbd> + <kbd>H</kbd> |
| Delete word right      | <kbd>⌥ Option</kbd> + <kbd>⌦ Del</kbd> **or** <kbd>Fn</kbd> + <kbd>⌥ Option</kbd> + <kbd>⌦ Del</kbd>    |
| Delete line            | <kbd>⇧ Shift</kbd> + <kbd>⌘ Cmd</kbd> + <kbd>K</kbd>                                                    |
| Delete to line start   | <kbd>⌘ Cmd</kbd> + <kbd>⌫ Backspace</kbd>                                                               |
| Delete to line end     | <kbd>⌘ Cmd</kbd> + <kbd>⌦ Del</kbd> **or** <kbd>^ Ctrl</kbd> + <kbd>K</kbd>                             |

**Linux**

| Action                 | Shortcut                                              |
| ---------------------- | ----------------------------------------------------- |
| Delete character left  | <kbd>⌫ Backspace</kbd>                                |
| Delete character right | <kbd>⌦ Del</kbd>                                      |
| Delete word left       | <kbd>^ Ctrl</kbd> + <kbd>⌫ Backspace</kbd>            |
| Delete word right      | <kbd>^ Ctrl</kbd> + <kbd>⌦ Del</kbd>                  |
| Delete line            | <kbd>⇧ Shift</kbd> + <kbd>^ Ctrl</kbd> + <kbd>K</kbd> |

### Line Operations

**Windows**

| Action               | Shortcut                                                                   |
| -------------------- | -------------------------------------------------------------------------- |
| Move line up         | <kbd>⎇ Alt</kbd> + <kbd>↑ Up</kbd>                                         |
| Move line down       | <kbd>⎇ Alt</kbd> + <kbd>↓ Down</kbd>                                       |
| Copy line up         | <kbd>⇧ Shift</kbd> + <kbd>⎇ Alt</kbd> + <kbd>↑ Up</kbd>                    |
| Copy line down       | <kbd>⇧ Shift</kbd> + <kbd>⎇ Alt</kbd> + <kbd>↓ Down</kbd>                  |
| Toggle line comment  | <kbd>^ Ctrl</kbd> + <kbd>/</kbd>                                           |
| Add line comment     | <kbd>^ Ctrl</kbd> + <kbd>K</kbd> **then** <kbd>^ Ctrl</kbd> + <kbd>C</kbd> |
| Remove line comment  | <kbd>^ Ctrl</kbd> + <kbd>K</kbd> **then** <kbd>^ Ctrl</kbd> + <kbd>U</kbd> |
| Toggle block comment | <kbd>⇧ Shift</kbd> + <kbd>⎇ Alt</kbd> + <kbd>A</kbd>                       |

**macOS**

| Action               | Shortcut                                                                 |
| -------------------- | ------------------------------------------------------------------------ |
| Move line up         | <kbd>⌥ Option</kbd> + <kbd>↑ Up</kbd>                                    |
| Move line down       | <kbd>⌥ Option</kbd> + <kbd>↓ Down</kbd>                                  |
| Copy line up         | <kbd>⇧ Shift</kbd> + <kbd>⌥ Option</kbd> + <kbd>↑ Up</kbd>               |
| Copy line down       | <kbd>⇧ Shift</kbd> + <kbd>⌥ Option</kbd> + <kbd>↓ Down</kbd>             |
| Toggle line comment  | <kbd>⌘ Cmd</kbd> + <kbd>/</kbd>                                          |
| Add line comment     | <kbd>⌘ Cmd</kbd> + <kbd>K</kbd> **then** <kbd>⌘ Cmd</kbd> + <kbd>C</kbd> |
| Remove line comment  | <kbd>⌘ Cmd</kbd> + <kbd>K</kbd> **then** <kbd>⌘ Cmd</kbd> + <kbd>U</kbd> |
| Toggle block comment | <kbd>⇧ Shift</kbd> + <kbd>⌥ Option</kbd> + <kbd>A</kbd>                  |
| Split line           | <kbd>^ Ctrl</kbd> + <kbd>O</kbd>                                         |
| Transpose characters | <kbd>^ Ctrl</kbd> + <kbd>T</kbd>                                         |

**Linux**

| Action               | Shortcut                                                                   |
| -------------------- | -------------------------------------------------------------------------- |
| Move line up         | <kbd>⎇ Alt</kbd> + <kbd>↑ Up</kbd>                                         |
| Move line down       | <kbd>⎇ Alt</kbd> + <kbd>↓ Down</kbd>                                       |
| Copy line up         | <kbd>⇧ Shift</kbd> + <kbd>⎇ Alt</kbd> + <kbd>↑ Up</kbd>                    |
| Copy line down       | <kbd>⇧ Shift</kbd> + <kbd>⎇ Alt</kbd> + <kbd>↓ Down</kbd>                  |
| Toggle line comment  | <kbd>^ Ctrl</kbd> + <kbd>/</kbd>                                           |
| Add line comment     | <kbd>^ Ctrl</kbd> + <kbd>K</kbd> **then** <kbd>^ Ctrl</kbd> + <kbd>C</kbd> |
| Remove line comment  | <kbd>^ Ctrl</kbd> + <kbd>K</kbd> **then** <kbd>^ Ctrl</kbd> + <kbd>U</kbd> |
| Toggle block comment | <kbd>⇧ Shift</kbd> + <kbd>⎇ Alt</kbd> + <kbd>A</kbd>                       |

### Autocomplete

**Windows**

| Action                      | Shortcut                                   |
| --------------------------- | ------------------------------------------ |
| Start completion            | <kbd>^ Ctrl</kbd> + <kbd>Space</kbd>       |
| Accept completion           | <kbd>Enter ⏎</kbd> **or** <kbd>Tab ⇥</kbd> |
| Close completion            | <kbd>⎋ Esc</kbd>                           |
| Navigate completion options | <kbd>↑ Up</kbd> **or** <kbd>↓ Down</kbd>   |

**macOS**

| Action                      | Shortcut                                   |
| --------------------------- | ------------------------------------------ |
| Start completion            | <kbd>^ Ctrl</kbd> + <kbd>Space</kbd>       |
| Accept completion           | <kbd>Enter ⏎</kbd> **or** <kbd>Tab ⇥</kbd> |
| Close completion            | <kbd>⎋ Esc</kbd>                           |
| Navigate completion options | <kbd>↑ Up</kbd> **or** <kbd>↓ Down</kbd>   |

**Linux**

| Action                      | Shortcut                                   |
| --------------------------- | ------------------------------------------ |
| Start completion            | <kbd>^ Ctrl</kbd> + <kbd>Space</kbd>       |
| Accept completion           | <kbd>Enter ⏎</kbd> **or** <kbd>Tab ⇥</kbd> |
| Close completion            | <kbd>⎋ Esc</kbd>                           |
| Navigate completion options | <kbd>↑ Up</kbd> **or** <kbd>↓ Down</kbd>   |

### Indentation

**Windows**

| Action      | Shortcut                                                                       |
| ----------- | ------------------------------------------------------------------------------ |
| Indent more | <kbd>Tab ⇥</kbd> **or** <kbd>^ Ctrl</kbd> + <kbd>]</kbd>                       |
| Indent less | <kbd>⇧ Shift</kbd> + <kbd>Tab ⇥</kbd> **or** <kbd>^ Ctrl</kbd> + <kbd>\[</kbd> |

**macOS**

| Action      | Shortcut                         |
| ----------- | -------------------------------- |
| Indent more | <kbd>⌘ Cmd</kbd> + <kbd>]</kbd>  |
| Indent less | <kbd>⌘ Cmd</kbd> + <kbd>\[</kbd> |

**Linux**

| Action      | Shortcut                                                                       |
| ----------- | ------------------------------------------------------------------------------ |
| Indent more | <kbd>Tab ⇥</kbd> **or** <kbd>^ Ctrl</kbd> + <kbd>]</kbd>                       |
| Indent less | <kbd>⇧ Shift</kbd> + <kbd>Tab ⇥</kbd> **or** <kbd>^ Ctrl</kbd> + <kbd>\[</kbd> |

### Code Folding

**Windows**

| Action      | Shortcut                                                                   |
| ----------- | -------------------------------------------------------------------------- |
| Fold code   | <kbd>^ Ctrl</kbd> + <kbd>⇧ Shift</kbd> + <kbd>\[</kbd>                     |
| Unfold code | <kbd>^ Ctrl</kbd> + <kbd>⇧ Shift</kbd> + <kbd>]</kbd>                      |
| Fold all    | <kbd>^ Ctrl</kbd> + <kbd>K</kbd> **then** <kbd>^ Ctrl</kbd> + <kbd>0</kbd> |
| Unfold all  | <kbd>^ Ctrl</kbd> + <kbd>K</kbd> **then** <kbd>^ Ctrl</kbd> + <kbd>J</kbd> |

**macOS**

| Action      | Shortcut                                                                  |
| ----------- | ------------------------------------------------------------------------- |
| Fold code   | <kbd>⌘ Cmd</kbd> + <kbd>⌥ Option</kbd> + <kbd>\[</kbd>                    |
| Unfold code | <kbd>⌘ Cmd</kbd> + <kbd>⌥ Option</kbd> + <kbd>]</kbd>                     |
| Fold all    | <kbd>⌘ Cmd</kbd> + <kbd>K</kbd> **then** <kbd>⌘ Cmd</kbd> + <kbd>0</kbd>  |
| Unfold all  | <kbd>⌘ Cmd</kbd> + <kbd>K</kbd> **then** <kbd>⌘ Cmd</kbd> + <kbd>J</kbd>  |

**Linux**

| Action      | Shortcut                                                                   |
| ----------- | -------------------------------------------------------------------------- |
| Fold code   | <kbd>^ Ctrl</kbd> + <kbd>⇧ Shift</kbd> + <kbd>\[</kbd>                     |
| Unfold code | <kbd>^ Ctrl</kbd> + <kbd>⇧ Shift</kbd> + <kbd>]</kbd>                      |
| Fold all    | <kbd>^ Ctrl</kbd> + <kbd>K</kbd> **then** <kbd>^ Ctrl</kbd> + <kbd>0</kbd> |
| Unfold all  | <kbd>^ Ctrl</kbd> + <kbd>K</kbd> **then** <kbd>^ Ctrl</kbd> + <kbd>J</kbd> |

### Multi-cursor

**Windows**

| Action                       | Shortcut                                                 |
| ---------------------------- | -------------------------------------------------------- |
| Add cursor at click position | <kbd>⎇ Alt</kbd> + <kbd>Left Button</kbd>                |
| Add cursor above             | <kbd>^ Ctrl</kbd> + <kbd>⎇ Alt</kbd> + <kbd>↑ Up</kbd>   |
| Add cursor below             | <kbd>^ Ctrl</kbd> + <kbd>⎇ Alt</kbd> + <kbd>↓ Down</kbd> |
| Add cursors to line ends     | <kbd>⇧ Shift</kbd> + <kbd>⎇ Alt</kbd> + <kbd>I</kbd>     |
| Clear multiple cursors       | <kbd>⎋ Esc</kbd>                                         |

**macOS**

| Action                       | Shortcut                                                    |
| ---------------------------- | ----------------------------------------------------------- |
| Add cursor at click position | <kbd>⌥ Option</kbd> + <kbd>Left Button</kbd>                |
| Add cursor above             | <kbd>^ Ctrl</kbd> + <kbd>⌥ Option</kbd> + <kbd>↑ Up</kbd>   |
| Add cursor below             | <kbd>^ Ctrl</kbd> + <kbd>⌥ Option</kbd> + <kbd>↓ Down</kbd> |
| Add cursors to line ends     | <kbd>⇧ Shift</kbd> + <kbd>⌥ Option</kbd> + <kbd>I</kbd>     |
| Clear multiple cursors       | <kbd>⎋ Esc</kbd>                                            |

**Linux**

| Action                       | Shortcut                                                 |
| ---------------------------- | -------------------------------------------------------- |
| Add cursor at click position | <kbd>⎇ Alt</kbd> + <kbd>Left Button</kbd>                |
| Add cursor above             | <kbd>^ Ctrl</kbd> + <kbd>⎇ Alt</kbd> + <kbd>↑ Up</kbd>   |
| Add cursor below             | <kbd>^ Ctrl</kbd> + <kbd>⎇ Alt</kbd> + <kbd>↓ Down</kbd> |
| Add cursors to line ends     | <kbd>⇧ Shift</kbd> + <kbd>⎇ Alt</kbd> + <kbd>I</kbd>     |
| Clear multiple cursors       | <kbd>⎋ Esc</kbd>                                         |

### Formatting

**Windows**

| Action          | Shortcut                                             |
| --------------- | ---------------------------------------------------- |
| Format document | <kbd>⇧ Shift</kbd> + <kbd>⎇ Alt</kbd> + <kbd>F</kbd> |

**macOS**

| Action          | Shortcut                                             |
| --------------- | ---------------------------------------------------- |
| Format document | <kbd>⇧ Shift</kbd> + <kbd>⌘ Cmd</kbd> + <kbd>F</kbd> |

**Linux**

| Action          | Shortcut                                              |
| --------------- | ----------------------------------------------------- |
| Format document | <kbd>^ Ctrl</kbd> + <kbd>⇧ Shift</kbd> + <kbd>I</kbd> |

### Search & Navigation
