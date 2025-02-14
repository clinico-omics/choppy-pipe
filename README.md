> Author: Jingcheng Yang
>
> Email: yjcyxky@163.com
>
> Date: 2018-12-13

# Choppy for Reproducible Omics Pipeline

[中文文档](http://docs.3steps.cn)

## Introduction

Choppy is a command-line & web tool for executing WDL workflows on Cromwell servers. (Based on widdler, but more.)
Features include:

- Workflow execution: Execute a workflow on a specified Cromwell server.
- Workflow restart: Restart a previously executed workflow.
- Workflow queries: Get the status, metadata, or logs for a specific workflow.
- Workflow result explanation: Get more detailed information on fails at the command line.
- Workflow monitoring: Monitor a specific workflow or set of user-specific workflows to completion.
- Workflow abortion: Abort a running workflow.
- JSON validation: Validate a JSON input file against the WDL file intended for use.

## Dependencies

Choppy requires Python 3+ and Java-1.8 to be loaded in your environment in order for full functionality to work.

## Installation

```
virtualenv .env
source .env/bin/activate
pip install choppy-0.2.0.tar.gz

# Activate bash auto-complete
activate-global-python-argcomplete
eval "$(register-python-argcomplete choppy)"
```

## Usage

Below is choppy's basic help text. Choppy expects one of three usage modes to
be indicated as it's first argument: run, query, or abort.

```
usage: choppy <positional argument> [<args>]

Description: A tool for executing and monitoring WDLs to Cromwell instances.

positional arguments:
  {restart,explain,log,abort,monitor,query,run,validate,label,email,upload,batch,testapp,install,apps}

optional arguments:
  -h, --help            show this help message and exit
```

### choppy submit

Below is choppy's submit help text. It expects the user to provide a wdl file,
json file, and to indicate one of the available servers for execution. The validate option
validates both the WDL and the JSON file submitted and is on by default.

```
usage: choppy submit <wdl file> <json file> [<args>]

Submit a WDL & JSON for execution on a Cromwell VM.

positional arguments:
  wdl                   Path to the WDL to be executed.
  json                  Path the json inputs file.

optional arguments:
  -h, --help            show this help message and exit
  -v, --validate        Validate WDL inputs in json file. (default: False)
  -l LABEL, --label LABEL
                        A key:value pair to assign. May be used multiple
                        times. (default: None)
  -m, --monitor         Monitor the workflow and receive an e-mail
                        notification when it terminates. (default: False)
  -i INTERVAL, --interval INTERVAL
                        If --monitor is selected, the amount of time in
                        seconds to elapse between status checks. (default: 30)
  -o EXTRA_OPTIONS, --extra_options EXTRA_OPTIONS
                        Additional workflow options to pass to Cromwell.
                        Specify as k:v pairs. May be specified multipletimes
                        for multiple options. See
                        https://github.com/broadinstitute/cromwell#workflow-
                        optionsfor available options. (default: None)
  -V, --verbose         If selected, choppy will write the current status to
                        STDOUT until completion while monitoring. (default:
                        False)
  -n, --no_notify       When selected, disable choppy e-mail notification of
                        workflow completion. (default: False)
  -d DEPENDENCIES, --dependencies DEPENDENCIES
                        A zip file containing one or more WDL files that the
                        main WDL imports. (default: None)
  -D, --disable_caching
                        Don\'t used cached data. (default: False)
  -S {localhost,remote}, --server {localhost,remote}
                        Choose a cromwell server from ['localhost','remote'] (default: None)
```

For example:

`choppy submit myworkflow.wdl myinput.json -S remote`

This will return a workflow ID and status if successfully submitted, for example:

`{'id': '2f8bb5c6-8254-4d38-b010-620913dd325e', 'status': 'Submitted'}`

This will execute a workflow that uses subworkflows:

`choppy submit myworkflow.wdl myinput.json -S remote -d mydependencies.zip`

Users may also invoke Choppy's monitoring capabilities when initiating a workflow. See below for an
explanation of monitoring options.

### choppy restart

If a workflow has been previously executed to a Cromwell server, it is possible to restart the workflow after it has
completed and run it again with the same inputs simply by providing the workflow ID and server of the original run.
The usage for performing this action is as follows:

```
usage: choppy restart <workflow id>

Restart a submitted workflow.

positional arguments:
  workflow_id           workflow id of workflow to restart.

optional arguments:
  -h, --help            show this help message and exit
  -S {localhost,remote}, --server {localhost,remote}
                        Choose a cromwell server from ['localhost','remote']
                        (default: None)
```

For example:

```
choppy restart b931c639-e73d-4b59-9333-be5ede4ae2cb -S remote
```

Will restart workflow b931xxx and return the new workflow id like so:

```
Workflow restarted successfully; new workflow-id: 164678b8-2a52-40f3-976c-417c777c78ef
```

Finally, any restarted workflows will inherit the labels of it's originating workflow.

### choppy query

Below is choppy's query help text. Aside from the workflow ID it expects one or more optional
arguments to request basic status, metadata, and/or logs.

```
usage: choppy query <workflow id> [<args>]

Query cromwell for information on the submitted workflow.

positional arguments:
  workflow_id           workflow id for workflow execution of interest.
                           (default: None)

optional arguments:
  -h, --help            show this help message and exit
  -s, --status          Print status for workflow to stdout (default: False)
  -m, --metadata        Print metadata for workflow to stdout (default: False)
  -l, --logs            Print logs for workflow to stdout (default: False)
  -u USERNAME, --username USERNAME
                       Owner of workflows to monitor. (default: amr)
  -L LABEL, --label LABEL
                       Query status of all workflows with specific label(s).
                       (default: None)
  -d DAYS, --days DAYS  Last n days to query. (default: 7)
  -S {localhost,remote}, --server {localhost,remote}
                       Choose a cromwell server from ['localhost','remote'] (default: None)
  -f {Running,Submitted,QueuedInCromwell,Failed,Aborted,Succeeded}, --filter {Running,Submitted,QueuedInCromwell,Failed,Aborted,Succeeded}
                       Filter by a workflow status from those listed above.
                       May be specified more than once. (default: None)
  -a, --all             Query for all users. (default: False)
```

For example:
`choppy 2f8bb5c6-8254-4d38-b010-620913dd325e query -s -S remote`

will return something like this:

`[{'id': '2f8bb5c6-8254-4d38-b010-620913dd325e', 'status': 'Running'}]`

and:

`choppy query 2f8bb5c6-8254-4d38-b010-620913dd325e -m -s -S remote`

will return a ton of information like so (truncated for viewability):

```
{'status': 'Running', 'submittedFiles': {'workflow': '# GATK WDL\r\n# import "hc_scatter.wdl" as sub\r\n\r\ntask VersionCheck {\r\n    String gatk\r\n    command {\r\n        source
/broad/software/scripts/useuse\r\n        use Java-1.8\r\n        use Python-2.7\r\n... 'ref': '/cil/shed/sandboxes/amr/dev/gatk_pipeline/output/pfal_5/Plasmodium_falciparum_3D7.fasta'}}]}, 'submi
ssion': '2017-07-14T11:26:05.931-04:00', 'workflowName': 'gatk', 'outputs': {}, 'id': '2f8bb5c6-8254-4d38-b010-620913dd325e'}]
```

and:

`choppy query 2f8bb5c6-8254-4d38-b010-620913dd325e -l -s -S remote`

```
[{'id': '2f8bb5c6-8254-4d38-b010-620913dd325e', 'calls': {'gatk.MakeSampleDir': [{'shardIndex': 0, 'attempt': 1, 'stderr': '/cil/shed/apps/internal/cromwell_new/cromwell-executions/ga
   tk/2f8bb5c6-8254-4d38-b010-620913dd325e/call-MakeSampleDir/shard-0/execution/stderr', 'stdout': '/cil/shed/apps/internal/cromwell_new/cromwell-executions/gatk/2f8bb5c6-8254-4d38-b010-
   620913dd325e/call-MakeSampleDir/shard-0/execution/stdout'}
```

### choppy abort

Below is choppy's abort usage. Simply provide the

```
usage: choppy abort <workflow id> <server>

Abort a submitted workflow.

positional arguments:
  workflow_id           workflow id of workflow to abort.

optional arguments:
  -h, --help            show this help message and exit
  -S {localhost,remote}, --server {localhost,remote}
                       Choose a cromwell server from ['localhost','remote']
                       (default: None)
```

This example:
`choppy abort 2f8bb5c6-8254-4d38-b010-620913dd325e -S remote`

will return:

```
{'status': 'Aborted', 'id': '2f8bb5c6-8254-4d38-b010-620913dd325e'}
```

### choppy explain

Running choppy explain will provide information at command line similar to the monitor e-mail, including workflow
status, root directory, stdout and stderr information, and useful links. Usage is as follows:

```
usage: choppy explain <workflowid>

Explain the status of a workflow.

positional arguments:
  workflow_id           workflow id of workflow to abort.

optional arguments:
  -h, --help            show this help message and exit
  -S {localhost,remote}, --server {localhost,remote}
                        Choose a cromwell server from ['localhost','remote']
                        (default: None)
```

This example:

```
choppy explain b931c639-e73d-4b59-9333-be5ede4ae2cb -S remote
```

will return:

```
-------------Workflow Status-------------
{'id': 'b931c639-e73d-4b59-9333-be5ede4ae2cb',
 'status': 'Failed',
 'workflowRoot': '/cil/shed/apps/internal/cromwell_gaag/cromwell-executions/gatk/b931c639-e73d-4b59-9333-be5ede4ae2cb'}
-------------Failed Stdout-------------
/cil/shed/apps/internal/cromwell_gaag/cromwell-executions/gatk/b931c639-e73d-4b59-9333-be5ede4ae2cb/call-ApplySnpRecalibration/execution/stdout:
[Errno 2] No such file or directory: u'/cil/shed/apps/internal/cromwell_gaag/cromwell-executions/gatk/b931c639-e73d-4b59-9333-be5ede4ae2cb/call-ApplySnpRecalibration/execution/stdout'
-------------Failed Stderr-------------
/cil/shed/apps/internal/cromwell_gaag/cromwell-executions/gatk/b931c639-e73d-4b59-9333-be5ede4ae2cb/call-ApplySnpRecalibration/execution/stderr:
[Errno 2] No such file or directory: u'/cil/shed/apps/internal/cromwell_gaag/cromwell-executions/gatk/b931c639-e73d-4b59-9333-be5ede4ae2cb/call-ApplySnpRecalibration/execution/stderr'
-------------Cromwell Links-------------
http://ale:9000/api/workflows/v1/b931c639-e73d-4b59-9333-be5ede4ae2cb/metadata
http://ale:9000/api/workflows/v1/b931c639-e73d-4b59-9333-be5ede4ae2cb/timing
```

Note that in this case, there were no stdout or stderr for the step that failed in the workflow.

## Validation

(Requires Java-1.8, so make sure to 'use Java-1.8' before trying validation)

Choppy validation attempts to validate the inputs in the user's supplied json file against the WDL
arguments in the supplied WDL file. Validation is OFF by default and so users must specify it using
the -v flag if using choppy submit. Validaton can also be performed using choppy validate if you
wish to validate inputs without executing the workflow.

It will validate the following:

- That the value of a parameter in the json matches the same type of value the WDL expects. For example
  if the WDL expects an integer and the parameter supplies a float, this will be flagged as an error.
- That if the parameter is of type File, that the file exists on the file system.
- If a parameter specified in the json is not expected by the WDL.
- If a parameter contains the string 'samples_file' it's value will be interpreted as an input TSV file in which
  the last column of every row indicates a sample file. In this case, an existence check will be made on each
  sample file.

It will NOT validate the following:

- The contents of arrays. It can't tell the difference between an array of strings and an array of integers, but
  it can tell they are arrays, and if a parameter expects an array but is provided something else this will
  be logged as an error.

A note on validating WDL files with dependencies: due to the limitations of the current implementation
of depedency validation, WDL file dependencies must be present in the same directory as the main WDL file
and must be unzipped. Otherwise validation may not work.

Validation may also be run as a stand-alone operation using choppy validate. Usage is as follows:

```
usage: choppy validate <wdl_file> <json_file>

Validate (but do not run) a json for a specific WDL file.

positional arguments:
  wdl         Path to the WDL associated with the json file.
  json        Path the json inputs file to validate.

optional arguments:
  -h, --help  show this help message and exit
```

For example:

`choppy mywdl.wdl myjson.json`

If the json file has errors, a list of errors will be reported in the same way that the runtime validation reports.
For example:

```
bad.json input file contains the following errors:
gatk.ts_filter_snp: 99 is not a valid Float.
gatk.tcir: False is not a valid Boolean. Note that JSON boolean values must not be quoted.
gatk.ploidy: 2.0 is not a valid Int.
Required parameter gatk.snp_annotation is missing from input json.
Required parameter gatk.ref_file is missing from input json.
```

### choppy log

Running 'choppy log' will print to screen the commands used by each task of a workflow. For example, running:

```
choppy log becb307f-4718-4d8b-836f-5780d64c4a82 -S remote
```

Results in the following:

```
{u'hello.helloWorld': [{u'attempt': 1, u'shardIndex': -1, u'stderr': u'/btl/store/cromwell_executions/hello/becb307f-4718-4d8b-836f-5780d64c4a82/call-helloWorld/execution/stderr', u'stdout': u'/btl/store/cromwell_executions/hello/becb307f-4718-4d8b-836f-5780d64c4a82/call-helloWorld/execution/stdout'}]}
hello.helloWorld:

#!/bin/bash
tmpDir=$(mktemp -d /cil/shed/apps/internal/cromwell_new/cromwell-executions/hello/d90bf4f3-d9fb-4f07-92d9-0d46c40355f1/call-helloWorld/execution/tmp.XXXXXX)
chmod 777 $tmpDir
export _JAVA_OPTIONS=-Djava.io.tmpdir=$tmpDir
export TMPDIR=$tmpDir

(
cd /cil/shed/apps/internal/cromwell_new/cromwell-executions/hello/d90bf4f3-d9fb-4f07-92d9-0d46c40355f1/call-helloWorld/execution
echo Hello, amr
)
echo $? > /cil/shed/apps/internal/cromwell_new/cromwell-executions/hello/d90bf4f3-d9fb-4f07-92d9-0d46c40355f1/call-helloWorld/execution/rc.tmp
(
cd /cil/shed/apps/internal/cromwell_new/cromwell-executions/hello/d90bf4f3-d9fb-4f07-92d9-0d46c40355f1/call-helloWorld/execution

)
sync
mv /cil/shed/apps/internal/cromwell_new/cromwell-executions/hello/d90bf4f3-d9fb-4f07-92d9-0d46c40355f1/call-helloWorld/execution/rc.tmp /cil/shed/apps/internal/cromwell_new/cromwell-executions/hello/d90bf4f3-d9fb-4f07-92d9-0d46c40355f1/call-helloWorld/execution/rc
```

### choppy monitor

Choppy allows the monitoring of workflow(s). Unlike the query options, monitoring persists until a workflow reaches
a terminal state (any state besides 'Running' or 'Submitted'). While monitoring, it can optionally print the status of
a workflow to the screen, and when a terminal state is reached, it can optionally e-mail the user (users are assumed
to be of the broadinstitute.org domain) when the workflow is finished.

Monitoring usage is as follows:

```
usage: choppy monitor <workflow_id> [<args>]

Monitor a particular workflow and notify user via e-mail upon completion. If
aworkflow ID is not provided, user-level monitoring is assumed.

positional arguments:
  workflow_id           workflow id for workflow to monitor. Do not specify if
                        user-level monitoring is desired. (default: None)

optional arguments:
  -h, --help            show this help message and exit
  -u USERNAME, --username USERNAME
                        Owner of workflows to monitor. (default: <your user name>)
  -i INTERVAL, --interval INTERVAL
                        Amount of time in seconds to elapse between status
                        checks. (default: 30)
  -V, --verbose         When selected, choppy will write the current status
                        to STDOUT until completion. (default: False)
  -n, --no_notify       When selected, disable choppy e-mail notification of
                        workflow completion. (default: False)
  -S {localhost,remote}, --server {localhost,remote}
                        Choose a cromwell server from ['localhost','remote']
                        (default: None)
```

#### Single Workflow Monitoring

Aside from monitoring of a single workflow with choppy's run command, you can also execute a monitor as in the
following example:

```
choppy monitor 7ff17cb3-12f1-4bf0-8754-e3a0d39178ea -S remote
```

In this case, choppy will continue to silently monitor this workflow until it detects a terminal status. An
e-mail will be sent to <user>@broadinstitute.org when a terminal status is detected, which will include
the metadata of the workflow.

If --verbose were selected, the user would have seen a STDOUT message indicating the workflows status at intervals
defined by the --interval parameter, which has a default of 30 seconds.

If --no_notify were selected, an e-mail would not be sent.

#### User Workflow Monitoring

(Note this feature is still under active development and is currently quite primitive)

User's may also monitor all workflows for a given user name by omitting the workflow_id parameter and specifying the
--user parameter like so:

```
choppy monitor -u amr -n -S remote
```

Here, the user 'amr' is monitoring all workflows ever executed by him using choppy. Any workflows not executed by
choppy will not be monitored. Workflows in a terminal state prior to execution will have an e-mail sent immediately
regarding their status, and any running workflows will result in an e-mail once they terminate. Using the --verbose
option here would result in STDOUT output for each workflow that is monitored at intervals specified by --interval.

## Logging

Choppy logs information in the application's logs directory in a file called choppy.log.
This can be useful to find information on choppy executions including workflow id and query
results and can help users locate workflow IDs if they've been lost. Each execution in the log
is presented like so, with the user's username indicated in the start/stop separators for
convenient identification.

```
-------------New Choppy Execution by amr-------------
2017-07-14 12:10:44,746 - choppy - INFO - Parameters chosen: {'logs': False, 'func': <function call_query at 0x00000000040B8378>, 'status': True, 'workflow_id': '7ff17cb3-12f1-4bf0-8754-e3a0d39178ea', 'server': 'btl-cromwell', 'metadata': False}
2017-07-14 12:10:44,746 - choppy.cromwell.Cromwell - INFO - URL:http://btl-cromwell:9000/api/workflows/v1
2017-07-14 12:10:44,746 - choppy.cromwell.Cromwell - INFO - Querying status for workflow 7ff17cb3-12f1-4bf0-8754-e3a0d39178ea
2017-07-14 12:10:44,747 - choppy.cromwell.Cromwell - INFO - GET REQUEST:http://btl-cromwell:9000/api/workflows/v1/7ff17cb3-12f1-4bf0-8754-e3a0d39178ea/status
2017-07-14 12:10:44,812 - choppy - INFO - Result: [{'id': '7ff17cb3-12f1-4bf0-8754-e3a0d39178ea', 'status': 'Running'}]
2017-07-14 12:10:44,813 - choppy - INFO -
-------------End Choppy Execution by amr-------------
```

## Roadmap

### 2018-12-12

- Add batch mode for batch submmitting WDL workflow.
- Add app repo. The apps are used repeatedly on some similar projects
