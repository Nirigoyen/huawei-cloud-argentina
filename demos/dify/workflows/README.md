# Workflows

This folder contains YAML (DSL) files for Dify workflows and apps to import into the deployed instance.

## DSL format

Dify uses a YAML format with the following structure:

```yaml
version: "0.6.0"        # DSL version
kind: app               # resource type
app:
  name: "My Workflow"
  description: "Workflow description"
  mode: workflow         # workflow | advanced-chat | agent | chat | completion
  icon: "🤖"
  icon_background: "#FFEAD5"
workflow:
  graph:
    nodes: []            # workflow nodes (start, llm, knowledge-retrieval, etc.)
    edges: []            # connections between nodes
  features: {}
```

The `ejemplo-workflow.yaml` file is an empty valid skeleton to use as a starting point.

## How to import

### Option 1: UI (recommended)

1. Open Dify in your browser (`terraform output -raw dify_url`).
2. Create the admin account if it's the first time.
3. **Create app** → **Import DSL** → upload the YAML file from this folder.

### Option 2: API (automation)

Use the `../scripts/import-dsl.sh` script:

```bash
../scripts/import-dsl.sh http://<EIP> admin@example.com password ejemplo-workflow.yaml
```

The script logs in against the Dify console API and imports the DSL via `POST /console/api/apps/imports`.

## Export existing workflows

To generate a YAML from a workflow already created in Dify: open the app → menu → **Export DSL**. The resulting YAML can be committed to this folder.
