# AIWF Command Line Interface (CLI) Reference

> **Notice for AI Agents:** This is the single source of truth for all `aiwf` CLI commands. Whenever you need to interact with the system (e.g. visual agent, memory, telegram, config, workflow), check the commands and syntax here before executing.

## Top-Level Commands
```text
AI Workflow Runtime Engine CLI
Usage: aiwf <command> [args] [--option=value ...]

  AGENT
    analysis-agent               Run analysis agent for code, architecture, or performance review

  CONFIG
    config                       Check and bootstrap AIWF runtime services configuration
    permission                   Manage agent permissions and authorization rules  (alias: permissions)
    registry                     Show registered commands and runtime registry state
    rules                        Show active AI_RULES.md and AGENTS.md policies

  DEPENDENCY
    conflict                     Detect and resolve dependency conflicts
    dependency                   Dependency graph analysis and validation
    deps                         Runtime dependency resolver commands
    merge                        Merge dependency resolution from multiple agents

  DOCS
    cleanup                      Run semantic documentation cleanup and folder migration
    migrate                      Migration tools for workflow artifacts and data  (alias: migration)

  KNOWLEDGE
    knowledge                    RAG vector knowledge base: index, query, status, rebuild
    search                       Query RAG vector knowledge base (shorthand for 'knowledge query')

  MEMORY
    env                          Show runtime environment variables and config
    mail                         Inter-session mail: send, read, list messages
    memory                       Project memory: bootstrap, update, query, status

  PROVIDER
    provider                     AI provider management: list, select, configure, test, usage

  RUNTIME
    execution                    Manage execution plans and running processes
    runtime                      Runtime daemon and process management

  SESSION
    complete                     Mark current phase as complete
    context                      Show or refresh current context health
    fail                         Mark current phase as failed
    heartbeat                    Update session heartbeat timestamp
    init                         Initialise AIWF workspace and install skills
    lock                         Manage workflow session lock
    resume                       Resume workflow from last checkpoint
    session                      Session management: show, clean, list, delete
    start                        Start a new workflow session checkpoint
    state                        Read/write workflow state files
    status                       Show current workflow session status
    step                         Update current step description and log
    usage                        Show context window usage, token counts, and budget
    validate                     Validate checkpoints, specs, and design artifacts

  SYSTEM
    api-server                   Start stable Observability API Server
    debug                        Debug tools: logs, state dump, diagnostics
    doctor                       Run workspace/framework diagnostics
    notify                       Send Telegram notification
    release                      Release pipeline: validate, tag, publish
    update                       Update AIWF framework, skills, and runtime components
    update-source                Update workflow-runtime source code from remote repository
    verify                       Verify implementation against blueprint

  TASK
    blueprint                    Generate or validate technical design blueprint
    compact                      Compact session context to reduce token usage
    implement                    Start implementation from an approved blueprint
    project                      Get cached project version info
    suggest                      Suggest next actions based on current workflow state
    task                         Task orchestration: create, list, update, complete tasks
    work-item                    Get cached work item info (fast, no lock needed)

  TELEGRAM
    telegram                     Global Telegram Shared Daemon: send, start, stop, link, config

  TESTING
    test                         Run test suite: unit, smoke, integration, real-runtime checks

  UI
    choice                       Present a numbered choice menu to the user
    input                        Read text input from user or stdin
    prompt                       Interactive prompt: select, confirm, input — for Blueprint approval gates

  VISUAL
    visual                       Visual Intelligence Runtime — capture, inspect, verify UI  (alias: vir, var)

  WORKFLOW
    active-workflow              Query and manage the currently active workflow
    classify                     Classify a user request into workflow intent
    coordinator                  Run workflow coordinator tick
    discover                     Discover available workflow skills and capabilities
    dispatch                     Dispatch an agent task
    orchestrator                 Run multi-agent orchestration pipeline  (alias: orchestrate)
    routing                      Show workflow routing and intent classification
    workflow                     Workflow lifecycle: create, run, status, history

Run 'aiwf <command> --help' for detailed options.
```

## Detailed Command Reference

### `aiwf analysis-agent`
- **Category:** AGENT
- **Aliases:** None
- **Requires Lock:** Yes

Run analysis agent for code, architecture, or performance review

```text
usage: aiwf analysis-agent [-h] [--target TARGET] [--output OUTPUT]
                           [--format {json,markdown,text}]
                           [{code,architecture,performance,security,accessibility}]

positional arguments:
  {code,architecture,performance,security,accessibility}

options:
  -h, --help            show this help message and exit
  --target TARGET       Target file or directory
  --output OUTPUT       Output report path
  --format {json,markdown,text}
```

---

### `aiwf config`
- **Category:** CONFIG
- **Aliases:** None
- **Requires Lock:** Yes

Check and bootstrap AIWF runtime services configuration

```text
usage: aiwf config [-h] {show,validate,reset,get,set} ...

positional arguments:
  {show,validate,reset,get,set}
    show                Show current config
    validate            Validate config file
    reset               Reset to defaults
    get                 Get a config key
    set                 Set a config key

options:
  -h, --help            show this help message and exit
```

---

### `aiwf permission`
- **Category:** CONFIG
- **Aliases:** permissions
- **Requires Lock:** No

Manage agent permissions and authorization rules

```text
usage: aiwf permission [-h] {list,status,grant,revoke} ...

positional arguments:
  {list,status,grant,revoke}
    list                List all permissions
    status              Current permission mode
    grant               Grant a permission
    revoke              Revoke a permission

options:
  -h, --help            show this help message and exit
```

---

### `aiwf registry`
- **Category:** CONFIG
- **Aliases:** None
- **Requires Lock:** No

Show registered commands and runtime registry state

```text
usage: aiwf registry [-h] [--format {json,table,text}]

options:
  -h, --help            show this help message and exit
  --format {json,table,text}
```

---

### `aiwf rules`
- **Category:** CONFIG
- **Aliases:** None
- **Requires Lock:** No

Show active AI_RULES.md and AGENTS.md policies

```text
usage: aiwf rules [-h] {status} ...

positional arguments:
  {status}

options:
  -h, --help  show this help message and exit
```

---

### `aiwf conflict`
- **Category:** DEPENDENCY
- **Aliases:** None
- **Requires Lock:** Yes

Detect and resolve dependency conflicts

```text
usage: aiwf conflict [-h] [--auto] [{detect,resolve,list}]

positional arguments:
  {detect,resolve,list}

options:
  -h, --help            show this help message and exit
  --auto                Auto-resolve conflicts
```

---

### `aiwf dependency`
- **Category:** DEPENDENCY
- **Aliases:** None
- **Requires Lock:** No

Dependency graph analysis and validation

```text
usage: aiwf dependency [-h] [--output OUTPUT] [{graph,validate,scan,report}]

positional arguments:
  {graph,validate,scan,report}

options:
  -h, --help            show this help message and exit
  --output OUTPUT       Output file path
```

---

### `aiwf deps`
- **Category:** DEPENDENCY
- **Aliases:** None
- **Requires Lock:** Yes

Runtime dependency resolver commands

```text
usage: aiwf deps [-h] [--skill SKILL] [--force] [--format {json,text,table}]
                 [{resolve,check,install,list,status}]

positional arguments:
  {resolve,check,install,list,status}

options:
  -h, --help            show this help message and exit
  --skill SKILL         Target skill name
  --force
  --format {json,text,table}
```

---

### `aiwf merge`
- **Category:** DEPENDENCY
- **Aliases:** None
- **Requires Lock:** Yes

Merge dependency resolution from multiple agents

```text
usage: aiwf merge [-h] [--from FROM_AGENT] [--strategy {latest,oldest,manual}]

options:
  -h, --help            show this help message and exit
  --from FROM_AGENT     Source agent ID
  --strategy {latest,oldest,manual}
```

---

### `aiwf cleanup`
- **Category:** DOCS
- **Aliases:** None
- **Requires Lock:** Yes

Run semantic documentation cleanup and folder migration

```text
usage: aiwf cleanup [-h] [--dry-run] [--target TARGET] [--backup]

options:
  -h, --help       show this help message and exit
  --dry-run        Preview changes without writing
  --target TARGET  Target directory to clean
  --backup         Create backup before cleanup
```

---

### `aiwf migrate`
- **Category:** DOCS
- **Aliases:** migration
- **Requires Lock:** Yes

Migration tools for workflow artifacts and data

```text
usage: aiwf migrate [-h] {state} ...

positional arguments:
  {state}
    state     Migrate state files to new schema

options:
  -h, --help  show this help message and exit
```

---

### `aiwf knowledge`
- **Category:** KNOWLEDGE
- **Aliases:** None
- **Requires Lock:** Yes

RAG vector knowledge base: index, query, status, rebuild

```text
usage: aiwf knowledge [-h] [--query QUERY] [--limit LIMIT]
                      [--provider {qdrant,sqlite,memory}]
                      [--collection COLLECTION] [--format {json,text}]
                      [{index,query,status,rebuild,clear,export}]

positional arguments:
  {index,query,status,rebuild,clear,export}
                        Knowledge action

options:
  -h, --help            show this help message and exit
  --query QUERY         Semantic search query
  --limit LIMIT         Max results (default: 5)
  --provider {qdrant,sqlite,memory}
                        Vector store provider
  --collection COLLECTION
                        Collection/index name
  --format {json,text}
```

---

### `aiwf search`
- **Category:** KNOWLEDGE
- **Aliases:** None
- **Requires Lock:** No

Query RAG vector knowledge base (shorthand for 'knowledge query')

```text
usage: aiwf search [-h] [--query QUERY_FLAG] [--limit LIMIT]
                   [--provider PROVIDER] [--format {json,text}]
                   [query]

positional arguments:
  query                 Search query string

options:
  -h, --help            show this help message and exit
  --query QUERY_FLAG    Search query (flag form)
  --limit LIMIT
  --provider PROVIDER   Vector store provider
  --format {json,text}
```

---

### `aiwf env`
- **Category:** MEMORY
- **Aliases:** None
- **Requires Lock:** No

Show runtime environment variables and config

```text
usage: aiwf env [-h] [--filter FILTER] [--json]

options:
  -h, --help       show this help message and exit
  --filter FILTER  Filter by key prefix
  --json           Output as JSON
```

---

### `aiwf mail`
- **Category:** MEMORY
- **Aliases:** None
- **Requires Lock:** Yes

Inter-session mail: send, read, list messages

```text
usage: aiwf mail [-h] [--to TO] [--message MESSAGE] {register,send,read,list}

positional arguments:
  {register,send,read,list}

options:
  -h, --help            show this help message and exit
  --to TO
  --message MESSAGE
```

---

### `aiwf memory`
- **Category:** MEMORY
- **Aliases:** None
- **Requires Lock:** Yes

Project memory: bootstrap, update, query, status

```text
usage: aiwf memory [-h] [--query QUERY] [--limit LIMIT]
                   [--format {json,text,table}]
                   [{bootstrap,update,query,status,reset,export}]

positional arguments:
  {bootstrap,update,query,status,reset,export}
                        Memory action to perform

options:
  -h, --help            show this help message and exit
  --query QUERY         Search query for memory lookup
  --limit LIMIT         Max results to return
  --format {json,text,table}
```

---

### `aiwf provider`
- **Category:** PROVIDER
- **Aliases:** None
- **Requires Lock:** Yes

AI provider management: list, select, configure, test, usage

```text
usage: aiwf provider [-h] [--name NAME] [--model MODEL] [--api-key API_KEY]
                     [--base-url BASE_URL] [--timeout TIMEOUT]
                     [--format {json,table,text}]
                     [{list,select,config,test,usage,status,reset,add,remove}]

positional arguments:
  {list,select,config,test,usage,status,reset,add,remove}
                        Provider action

options:
  -h, --help            show this help message and exit
  --name NAME           Provider name
  --model MODEL         Model name
  --api-key API_KEY     API key (stored securely)
  --base-url BASE_URL   Custom base URL
  --timeout TIMEOUT
  --format {json,table,text}
```

---

### `aiwf execution`
- **Category:** RUNTIME
- **Aliases:** None
- **Requires Lock:** Yes

Manage execution plans and running processes

```text
usage: aiwf execution [-h] {list,status,cancel,log} ...

positional arguments:
  {list,status,cancel,log}
    list                List active executions
    status              Current execution status
    cancel              Cancel running execution
    log                 Show execution log

options:
  -h, --help            show this help message and exit
```

---

### `aiwf runtime`
- **Category:** RUNTIME
- **Aliases:** None
- **Requires Lock:** Yes

Runtime daemon and process management

```text
usage: aiwf runtime [-h] {start,stop,status,restart,process} ...

positional arguments:
  {start,stop,status,restart,process}
    start               Start runtime daemon
    stop                Stop runtime daemon
    status              Daemon status
    restart             Restart daemon
    process             Process management

options:
  -h, --help            show this help message and exit
```

---

### `aiwf complete`
- **Category:** SESSION
- **Aliases:** None
- **Requires Lock:** Yes

Mark current phase as complete

```text
usage: aiwf complete [-h] [--checkpoint CHECKPOINT] [--step STEP]
                     [--next-skill NEXT_SKILL] [--next-command NEXT_COMMAND]

options:
  -h, --help            show this help message and exit
  --checkpoint CHECKPOINT
  --step STEP
  --next-skill NEXT_SKILL
  --next-command NEXT_COMMAND
```

---

### `aiwf context`
- **Category:** SESSION
- **Aliases:** None
- **Requires Lock:** No

Show or refresh current context health

```text
usage: aiwf context [-h] [--refresh] [--format {json,text}]

options:
  -h, --help            show this help message and exit
  --refresh
  --format {json,text}
```

---

### `aiwf fail`
- **Category:** SESSION
- **Aliases:** None
- **Requires Lock:** Yes

Mark current phase as failed

```text
usage: aiwf fail [-h] [--step STEP] [--log LOG]

options:
  -h, --help   show this help message and exit
  --step STEP
  --log LOG
```

---

### `aiwf heartbeat`
- **Category:** SESSION
- **Aliases:** None
- **Requires Lock:** No

Update session heartbeat timestamp

```text
usage: aiwf heartbeat [-h]

options:
  -h, --help  show this help message and exit
```

---

### `aiwf init`
- **Category:** SESSION
- **Aliases:** None
- **Requires Lock:** Yes

Initialise AIWF workspace and install skills

```text
usage: aiwf init [-h] [--force] [--skill SKILL] [--template TEMPLATE]
                 [--no-git] [--quiet]

options:
  -h, --help           show this help message and exit
  --force              Force re-initialise existing workspace
  --skill SKILL        Install specific skill only
  --template TEMPLATE  Workspace template to use
  --no-git             Skip git repository setup
  --quiet              Minimal output
```

---

### `aiwf lock`
- **Category:** SESSION
- **Aliases:** None
- **Requires Lock:** Yes

Manage workflow session lock

```text
usage: aiwf lock [-h] {acquire,release,status,force-release}

positional arguments:
  {acquire,release,status,force-release}

options:
  -h, --help            show this help message and exit
```

---

### `aiwf resume`
- **Category:** SESSION
- **Aliases:** None
- **Requires Lock:** Yes

Resume workflow from last checkpoint

```text
usage: aiwf resume [-h]

options:
  -h, --help  show this help message and exit
```

---

### `aiwf session`
- **Category:** SESSION
- **Aliases:** None
- **Requires Lock:** Yes

Session management: show, clean, list, delete

```text
usage: aiwf session [-h] {show,list,clean,delete} ...

positional arguments:
  {show,list,clean,delete}
    show                Show active session info
    list                List all sessions
    clean               Clean stale sessions
    delete              Delete a session

options:
  -h, --help            show this help message and exit
```

---

### `aiwf start`
- **Category:** SESSION
- **Aliases:** None
- **Requires Lock:** Yes

Start a new workflow session checkpoint

```text
usage: aiwf start [-h] --skill SKILL --command COMMAND
                  [--checkpoint CHECKPOINT] [--step STEP]

options:
  -h, --help            show this help message and exit
  --skill SKILL         Skill name to start
  --command COMMAND     Command being executed
  --checkpoint CHECKPOINT
  --step STEP
```

---

### `aiwf state`
- **Category:** SESSION
- **Aliases:** None
- **Requires Lock:** Yes

Read/write workflow state files

```text
usage: aiwf state [-h] {show,reset,export,get,set} ...

positional arguments:
  {show,reset,export,get,set}
    show                Show current state
    reset               Reset state to initial
    export              Export state to JSON
    get                 Get a state key
    set                 Set a state key

options:
  -h, --help            show this help message and exit
```

---

### `aiwf status`
- **Category:** SESSION
- **Aliases:** None
- **Requires Lock:** No

Show current workflow session status

```text
usage: aiwf status [-h]

options:
  -h, --help  show this help message and exit
```

---

### `aiwf step`
- **Category:** SESSION
- **Aliases:** None
- **Requires Lock:** Yes

Update current step description and log

```text
usage: aiwf step [-h] --step STEP [--log LOG]

options:
  -h, --help   show this help message and exit
  --step STEP  Step description
  --log LOG    Log message
```

---

### `aiwf usage`
- **Category:** SESSION
- **Aliases:** None
- **Requires Lock:** No

Show context window usage, token counts, and budget

```text
usage: aiwf usage [-h] [--format {json,table,text}] [--history]
                  [--provider PROVIDER] [--limit LIMIT]

options:
  -h, --help            show this help message and exit
  --format {json,table,text}
  --history             Show usage history
  --provider PROVIDER   Filter by provider
  --limit LIMIT
```

---

### `aiwf validate`
- **Category:** SESSION
- **Aliases:** None
- **Requires Lock:** No

Validate checkpoints, specs, and design artifacts

```text
usage: aiwf validate [-h] [--checkpoint CHECKPOINT] [--spec SPEC] [--strict]

options:
  -h, --help            show this help message and exit
  --checkpoint CHECKPOINT
                        Checkpoint number to validate
  --spec SPEC           Spec file path
  --strict
```

---

### `aiwf api-server`
- **Category:** SYSTEM
- **Aliases:** None
- **Requires Lock:** No

Start stable Observability API Server

```text
usage: aiwf api-server [-h] [--port PORT] [--host HOST] [--debug]

options:
  -h, --help   show this help message and exit
  --port PORT
  --host HOST
  --debug
```

---

### `aiwf debug`
- **Category:** SYSTEM
- **Aliases:** None
- **Requires Lock:** No

Debug tools: logs, state dump, diagnostics

```text
usage: aiwf debug [-h] [--tail TAIL] [{logs,state,session,memory,env}]

positional arguments:
  {logs,state,session,memory,env}

options:
  -h, --help            show this help message and exit
  --tail TAIL
```

---

### `aiwf doctor`
- **Category:** SYSTEM
- **Aliases:** None
- **Requires Lock:** No

Run workspace/framework diagnostics

```text
usage: aiwf doctor [-h] [--fix] [--verbose] [--check CHECK]

options:
  -h, --help     show this help message and exit
  --fix          Auto-fix issues
  --verbose
  --check CHECK  Run specific check only
```

---

### `aiwf notify`
- **Category:** SYSTEM
- **Aliases:** None
- **Requires Lock:** Yes

Send Telegram notification

```text
usage: aiwf notify [-h] --message MESSAGE
                   [--level {info,warning,error,success}]

options:
  -h, --help            show this help message and exit
  --message, -m MESSAGE
  --level {info,warning,error,success}
```

---

### `aiwf release`
- **Category:** SYSTEM
- **Aliases:** None
- **Requires Lock:** Yes

Release pipeline: validate, tag, publish

```text
usage: aiwf release [-h] [--version VERSION] [--dry-run]
                    [{validate,tag,publish,rollback,status}]

positional arguments:
  {validate,tag,publish,rollback,status}

options:
  -h, --help            show this help message and exit
  --version VERSION
  --dry-run
```

---

### `aiwf update`
- **Category:** SYSTEM
- **Aliases:** None
- **Requires Lock:** No

Update AIWF framework, skills, and runtime components

```text
usage: aiwf update [-h] [--force] [--dry-run] [--version VERSION]
                   [{framework,skills,runtime,all}]

positional arguments:
  {framework,skills,runtime,all}

options:
  -h, --help            show this help message and exit
  --force
  --dry-run
  --version VERSION     Target version
```

---

### `aiwf update-source`
- **Category:** SYSTEM
- **Aliases:** None
- **Requires Lock:** No

Update workflow-runtime source code from remote repository

```text
usage: aiwf update-source [-h] [--branch BRANCH] [--tag TAG] [--dry-run]
                          [--no-install]

options:
  -h, --help       show this help message and exit
  --branch BRANCH  Target branch
  --tag TAG        Target tag
  --dry-run
  --no-install     Skip pip install after update
```

---

### `aiwf verify`
- **Category:** SYSTEM
- **Aliases:** None
- **Requires Lock:** No

Verify implementation against blueprint

```text
usage: aiwf verify [-h] [--blueprint BLUEPRINT] [--strict]

options:
  -h, --help            show this help message and exit
  --blueprint BLUEPRINT
                        Blueprint file path
  --strict
```

---

### `aiwf blueprint`
- **Category:** TASK
- **Aliases:** None
- **Requires Lock:** Yes

Generate or validate technical design blueprint

```text
usage: aiwf blueprint [-h] [--work-item WORK_ITEM] [--skill SKILL]
                      [{generate,validate,freeze,status}]

positional arguments:
  {generate,validate,freeze,status}

options:
  -h, --help            show this help message and exit
  --work-item WORK_ITEM
                        Work item ID
  --skill SKILL         Target skill
```

---

### `aiwf compact`
- **Category:** TASK
- **Aliases:** None
- **Requires Lock:** Yes

Compact session context to reduce token usage

```text
usage: aiwf compact [-h] [--target-tokens TARGET_TOKENS]

options:
  -h, --help            show this help message and exit
  --target-tokens TARGET_TOKENS
```

---

### `aiwf implement`
- **Category:** TASK
- **Aliases:** None
- **Requires Lock:** Yes

Start implementation from an approved blueprint

```text
usage: aiwf implement [-h] --blueprint BLUEPRINT [--dry-run]

options:
  -h, --help            show this help message and exit
  --blueprint BLUEPRINT
                        Blueprint file path
  --dry-run
```

---

### `aiwf project`
- **Category:** TASK
- **Aliases:** None
- **Requires Lock:** No

Get cached project version info

```text
usage: aiwf project [-h] [--format {json,text}]

options:
  -h, --help            show this help message and exit
  --format {json,text}
```

---

### `aiwf suggest`
- **Category:** TASK
- **Aliases:** None
- **Requires Lock:** Yes

Suggest next actions based on current workflow state

```text
usage: aiwf suggest [-h] [--limit LIMIT]

options:
  -h, --help     show this help message and exit
  --limit LIMIT
```

---

### `aiwf task`
- **Category:** TASK
- **Aliases:** None
- **Requires Lock:** Yes

Task orchestration: create, list, update, complete tasks

```text
usage: aiwf task [-h] {list,status,create,update} ...

positional arguments:
  {list,status,create,update}
    list                List tasks
    status              Task status
    create              Create a task
    update              Update a task

options:
  -h, --help            show this help message and exit
```

---

### `aiwf work-item`
- **Category:** TASK
- **Aliases:** None
- **Requires Lock:** No

Get cached work item info (fast, no lock needed)

```text
usage: aiwf work-item [-h] [--id ID] [--format {json,text}]

options:
  -h, --help            show this help message and exit
  --id ID               Work item ID
  --format {json,text}
```

---

### `aiwf telegram`
- **Category:** TELEGRAM
- **Aliases:** None
- **Requires Lock:** Yes

Global Telegram Shared Daemon: send, start, stop, link, config

```text
usage: aiwf telegram [-h] action ...

positional arguments:
  action
    send      Send a Telegram message
    notify    Send notification (alias for send)
    start     Start the Telegram daemon
    stop      Stop the Telegram daemon
    status    Show daemon status
    restart   Restart the daemon
    link      Link Telegram account (interactive)
    config    Interactive step-by-step credential setup
    test      Send a test message to verify setup

options:
  -h, --help  show this help message and exit
```

---

### `aiwf test`
- **Category:** TESTING
- **Aliases:** None
- **Requires Lock:** Yes

Run test suite: unit, smoke, integration, real-runtime checks

```text
usage: aiwf test [-h] [--verbose] [--fail-fast] [--output OUTPUT]
                 [--filter FILTER] [--log LOG]
                 [{unit,smoke,integration,all,real}]

positional arguments:
  {unit,smoke,integration,all,real}
                        Test scope (default: smoke)

options:
  -h, --help            show this help message and exit
  --verbose, -v
  --fail-fast           Stop on first failure
  --output OUTPUT       Output report path
  --filter, -k FILTER   Filter tests by name pattern
  --log LOG             Log file path (default: .agents/runtime/tests.log)
```

---

### `aiwf choice`
- **Category:** UI
- **Aliases:** None
- **Requires Lock:** Yes

Present a numbered choice menu to the user

```text
usage: aiwf choice [-h] [--title TITLE] --options OPTIONS [--default DEFAULT]

options:
  -h, --help         show this help message and exit
  --title TITLE      Menu title
  --options OPTIONS  Newline or pipe-separated choices
  --default DEFAULT
```

---

### `aiwf input`
- **Category:** UI
- **Aliases:** None
- **Requires Lock:** No

Read text input from user or stdin

```text
usage: aiwf input [-h] {submit} ...

positional arguments:
  {submit}

options:
  -h, --help  show this help message and exit
```

---

### `aiwf prompt`
- **Category:** UI
- **Aliases:** None
- **Requires Lock:** No

Interactive prompt: select, confirm, input — for Blueprint approval gates

```text
usage: aiwf prompt [-h] {select,confirm} ...

positional arguments:
  {select,confirm}
    select          Show a selection prompt
    confirm         Show a yes/no confirmation

options:
  -h, --help        show this help message and exit
```

---

### `aiwf visual`
- **Category:** VISUAL
- **Aliases:** vir, var
- **Requires Lock:** Yes

Visual Intelligence Runtime — capture, inspect, verify UI

```text
usage: aiwf visual [-h] {agent,investigate,verify,memory,report,observe} ...

positional arguments:
  {agent,investigate,verify,memory,report,observe}

options:
  -h, --help            show this help message and exit
```

---

### `aiwf active-workflow`
- **Category:** WORKFLOW
- **Aliases:** None
- **Requires Lock:** Yes

Query and manage the currently active workflow

```text
usage: aiwf active-workflow [-h] [--json]

options:
  -h, --help  show this help message and exit
  --json
```

---

### `aiwf classify`
- **Category:** WORKFLOW
- **Aliases:** None
- **Requires Lock:** Yes

Classify a user request into workflow intent

```text
usage: aiwf classify [-h] --request REQUEST

options:
  -h, --help         show this help message and exit
  --request REQUEST  User request to classify
```

---

### `aiwf coordinator`
- **Category:** WORKFLOW
- **Aliases:** None
- **Requires Lock:** Yes

Run workflow coordinator tick

```text
usage: aiwf coordinator [-h]

options:
  -h, --help  show this help message and exit
```

---

### `aiwf discover`
- **Category:** WORKFLOW
- **Aliases:** None
- **Requires Lock:** Yes

Discover available workflow skills and capabilities

```text
usage: aiwf discover [-h]

options:
  -h, --help  show this help message and exit
```

---

### `aiwf dispatch`
- **Category:** WORKFLOW
- **Aliases:** None
- **Requires Lock:** Yes

Dispatch an agent task

```text
usage: aiwf dispatch [-h] --agent AGENT [--task TASK] [--skill SKILL]

options:
  -h, --help     show this help message and exit
  --agent AGENT  Agent role to dispatch
  --task TASK    Task description
  --skill SKILL  Target skill
```

---

### `aiwf orchestrator`
- **Category:** WORKFLOW
- **Aliases:** orchestrate
- **Requires Lock:** Yes

Run multi-agent orchestration pipeline

```text
usage: aiwf orchestrator [-h] [--work-item WORK_ITEM]
                         [{run,status,cancel,resume}]

positional arguments:
  {run,status,cancel,resume}

options:
  -h, --help            show this help message and exit
  --work-item WORK_ITEM
                        Work item ID
```

---

### `aiwf routing`
- **Category:** WORKFLOW
- **Aliases:** None
- **Requires Lock:** No

Show workflow routing and intent classification

```text
usage: aiwf routing [-h] [--intent INTENT]

options:
  -h, --help       show this help message and exit
  --intent INTENT  Raw intent to classify
```

---

### `aiwf workflow`
- **Category:** WORKFLOW
- **Aliases:** None
- **Requires Lock:** Yes

Workflow lifecycle: create, run, status, history

```text
usage: aiwf workflow [-h] {status,history,create} ...

positional arguments:
  {status,history,create}
    status              Current workflow status
    history             Workflow execution history
    create              Create new workflow

options:
  -h, --help            show this help message and exit
```

---

