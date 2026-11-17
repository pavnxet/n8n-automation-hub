<!-- n8n built-in node reference: n8n-nodes-base.scheduletrigger | source: https://docs.n8n.io/integrations/builtin/core-nodes/n8n-nodes-base.scheduletrigger -->

Use the Schedule Trigger node to run workflows at fixed intervals and times. This works in a similar way to the Cron software utility in Unix-like systems.

> **You must publish the workflow:**
> If a workflow uses the Schedule node as a trigger, make sure that you save and publish the workflow.

## Node parameters

Add **Trigger Rules** to determine when the trigger should run.

Use the **Trigger Interval** to select the time interval unit of measure to schedule the trigger for. All other parameters depend on the interval you select. Choose from:

- [Seconds trigger interval](#seconds-trigger-interval)
- [Minutes trigger interval](#minutes-trigger-interval)
- [Hours trigger interval](#hours-trigger-interval)
- [Days trigger interval](#days-trigger-interval)
- [Weeks trigger interval](#weeks-trigger-interval)
- [Months trigger interval](#months-trigger-interval)
- [Custom (Cron) interval](#custom-cron-interval)

You can add multiple **Trigger Rules** to run the node on different schedules.

Refer to the sections below for more detail on configuring each **Trigger Interval**. Refer to [Templates and examples](#templates-and-examples) for further examples.

> **Default timing from n8n 2.45.0:**
> Schedule Trigger nodes use the durable scheduler by default, as long as `N8N_USE_WORKFLOW_PUBLICATION_SERVICE` stays on (its default). The Seconds and Minutes trigger intervals run at uniform intervals measured from workflow publication, rather than on clock boundaries. Custom (Cron) intervals keep their timing. See [Schedule Trigger timing](https://app.gitbook.com/s/jm0ZYRpZIPWge2ZSiDYO/host-n8n/configure-n8n/durable-scheduler#trigger-node-mode) for clock-aligned timing, or [Use the in-memory scheduler](https://app.gitbook.com/s/jm0ZYRpZIPWge2ZSiDYO/host-n8n/configure-n8n/durable-scheduler#use-the-in-memory-scheduler) to switch schedulers.

### Seconds trigger interval

* **Seconds Between Triggers**: Enter the number of seconds between each workflow trigger. For example, if you enter `30` here, the trigger will run every 30 seconds.

### Minutes trigger interval

* **Minutes Between Triggers**: Enter the number of minutes between each workflow trigger. For example, if you enter `5` here, the trigger will run every 5 minutes.

### Hours trigger interval

* **Hours Between Triggers**: Enter the number of hours between each workflow trigger.
* **Trigger at Minute**: Enter the minute past the hour to trigger the node when it runs, from `0` to `59`.

For example, if you enter `6` **Hours Between Triggers** and `30` **Trigger at Minute**, the node will run every six hours at 30 minutes past the hour.

### Days trigger interval

* **Days Between Triggers**: Enter the number of days between each workflow trigger.
* **Trigger at Hour**: Select the hour of the day to trigger the node.
* **Trigger at Minute**: Enter the minute past the hour to trigger the node when it runs, from `0` to `59`.

For example, if you enter `2` **Days Between Triggers**, **9am** for **Trigger at Hour**, and `15` **Trigger at Minute**, the node will run every two days at 9:15am.

### Weeks trigger interval

* **Weeks Between Triggers**: Enter the number of weeks between each workflow trigger.
* **Trigger on Weekdays**: Select the day(s) of the week you want to trigger the node.
* **Trigger at Hour**: Select the hour of the day to trigger the node.
* **Trigger at Minute**: Enter the minute past the hour to trigger the node when it runs, from `0` to `59`.

For example, if you enter `2` **Weeks Between Triggers**, **Monday** for **Trigger on Weekdays**, **3pm** for **Trigger at Hour**, and `30` **Trigger at Minute**, the node will run every two weeks on Monday at 3:30 PM.

### Months trigger interval

* **Months Between Triggers**: Enter the number of months between each workflow trigger.
* **Trigger at Day of Month**: Enter the day of the month the day should trigger at, from `1` to `31`. If a month doesn't have this day, the node won't trigger. For example, if you enter `30` here, the node won't trigger in February.
* **Trigger at Hour**: Select the hour of the day to trigger the node.
* **Trigger at Minute**: Enter the minute past the hour to trigger the node when it runs, from `0` to `59`.

For example, if you enter `3` **Months Between Triggers**, `28` **Trigger at Day of Month**, **9am** for **Trigger at Hour**, and `0` **Trigger at Minute**, the node will run each quarter on the 28th day of the month at 9:00 AM.

### Custom (Cron) interval

Enter a custom cron **Expression** to set the schedule for the trigger.

To generate a Cron expression, you can use [crontab guru](https://crontab.guru). Paste the Cron expression that you generated using crontab guru in the **Expression** field in n8n.

#### Examples

|Type|Cron Expression|Description|
|---|---|---|
|Every X Seconds|`*/10 * * * * *`|Every 10 seconds.|
|Every X Minutes|`*/5 * * * *`|Every 5 minutes.|
|Hourly|`0 * * * *`|Every hour on the hour.|
|Daily|`0 6 * * *`|At 6:00 AM every day.|
|Weekly|`0 12 * * 1`|At noon every Monday.|
|Monthly|`0 0 1 * *`|At midnight on the 1st of every month.|
|Every X Days|`0 0 */3 * *`|At midnight every 3rd day.|
|Only Weekdays|`0 9 * * 1-5`|At 9:00 AM Monday through Friday.|
|Custom Hourly Range|`0 9-17 * * *`|Every hour from 9:00 AM to 5:00 PM every day.|
|Quarterly|`0 0 1 1,4,7,10 *`|At midnight on the 1st of January, April, July, and October.|

> **Using variables in the Cron expression:**
> While variables can be used in the scheduled trigger, their values only get evaluated when the workflow is published. If you alter a variable's value in the settings after a workflow is published, the changes won't alter the cron schedule. To re-evaluate the variable, unpublish the workflow and then re-publish it.

#### Why there are six asterisks in the Cron expression

The sixth asterisk in the Cron expression represents seconds. Setting this is optional. The node will execute even if you don't set the value for seconds.

|  (*)  |  *  |  *  |  *  |  *  |  *  |
|:--:|:--:|:--:|:--:|:--:|:--:|
|(second)|minute|hour|day of month|month|day of week(Sun-Sat)|

## Node options

The node's **Settings** tab offers options controlling what happens when an execution misses its scheduled time, for example because the instance was down:

* **If Execution Is Missed**: What to do with missed executions. Choose from:
    * **Don't Run Missed Executions** (default): Discard missed executions and resume on schedule.
    * **Run the Most Recent Missed Execution**: Run a single catch-up execution at the most recent missed time, then resume on schedule.
    * **Run the Most Recent Missed Execution Per Rule**: Like the previous option, but each trigger rule runs its own catch-up execution.
* **Missed Execution Grace Period (Seconds)**: How late an execution may start before it counts as missed. Set to `0` to use the instance setting (`N8N_SCHEDULER_MISFIRE_GRACE`, 60 seconds by default). n8n raises values below the instance minimum (60 seconds with the defaults) to it, and caps values above 30 days.

> **Feature availability:**
> These options are available from n8n 2.36, on Schedule Trigger nodes added from that version on. They take effect only when the instance runs the [durable scheduler](https://app.gitbook.com/s/jm0ZYRpZIPWge2ZSiDYO/host-n8n/configure-n8n/durable-scheduler), which is on by default from n8n 2.45.0. If you set `N8N_SCHEDULER_ENABLED=false`, Schedule Trigger nodes use the in-memory scheduler, which never runs missed executions.

## Templates and examples

[Browse n8n-nodes-base.scheduletrigger integration templates](https://n8n.io/integrations/schedule-trigger) or [search all templates](https://n8n.io/workflows/)

## Common issues

For common questions or issues and suggested solutions, refer to [Common Issues](https://docs.n8n.io/integrations/builtin/core-nodes/n8n-nodes-base.scheduletrigger/common-issues).

---

## Schedule Trigger node common issues

## Common issues

Here are some common errors and issues with the [Schedule Trigger node](https://docs.n8n.io/integrations/builtin/core-nodes/n8n-nodes-base.scheduletrigger) and steps to resolve or troubleshoot them.

### Invalid cron expression

This error occurs when you set **Trigger Interval** to **Custom (Cron)** and n8n doesn't understand your cron expression. This may mean that there is a mistake in your cron expression or that you're using an incompatible syntax.

To debug, check that the following:

* That your cron expression follows the syntax used in the [cron examples](https://docs.n8n.io/integrations/builtin/core-nodes/n8n-nodes-base.scheduletrigger#custom-cron-interval)
* That your cron expression (after removing the [seconds column](https://docs.n8n.io/integrations/builtin/core-nodes/n8n-nodes-base.scheduletrigger#why-there-are-six-asterisks-in-the-cron-expression)) validates on [crontab guru](https://crontab.guru/)

### Scheduled workflows run at the wrong time

If the Schedule Trigger node runs at the wrong time, it may mean that you need to adjust the time zone n8n uses.

#### Adjust the timezone globally

If you're using [n8n Cloud](https://app.gitbook.com/s/jm0ZYRpZIPWge2ZSiDYO/use-n8n-cloud), follow the instructions on the [set the Cloud instance timezone](https://app.gitbook.com/s/jm0ZYRpZIPWge2ZSiDYO/use-n8n-cloud/configure-cloud/set-your-timezone) page to ensure that n8n executes in sync with your local time.

If you're [self hosting](https://app.gitbook.com/s/jm0ZYRpZIPWge2ZSiDYO/host-n8n), set your global timezone using the [`GENERIC_TIMEZONE` environment variable](https://app.gitbook.com/s/jm0ZYRpZIPWge2ZSiDYO/host-n8n/configure-n8n/basic-configuration/use-environment-variables/timezone-and-localization).

#### Adjust the timezone for an individual workflow

To set the timezone for an individual workflow:

1. Open the workflow on the canvas.
2. Select the  **Workflow menu** in the upper-right corner.
3. Select **Settings**.
4. Change the **Timezone** setting.
5. Select **Save**.

#### Variables not working as expected

While variables can be used in the scheduled trigger, their values only get evaluated when the workflow is published. After publishing the workflow, you can alter a variable's value in the settings but it won't change how often the workflow runs. To work around this, you must stop and then publish a new version of the workflow to apply the updated variable value.

#### Changing the trigger interval

You can update the scheduled trigger interval at any time but it only gets updated when the workflow is published. If you change the trigger interval after the workflow is published, the changes won't take effect until you unpublish the workflow and then publish a new version of the workflow.

Also, the schedule begins from the time when you publish the workflow. For example, if you had originally set a schedule of every 1 hour and it should execute at 12:00, if you changed it to a 2 hour schedule and publish a new version of the workflow at 11:30, the next execution will be at 13:30, 2 hours from when you published it.
