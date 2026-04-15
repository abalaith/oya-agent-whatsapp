---
name: retool
display_name: "Retool"
description: "Query Retool databases (read-only) — run SELECT queries and list tables"
category: productivity
icon: database
skill_type: sandbox
catalog_type: addon
requirements: "psycopg2-binary"
resource_requirements:
  - env_var: RETOOL_DB_URL
    name: "Retool Database URL"
    description: "PostgreSQL connection string for Retool Database (e.g. postgresql://user:pass@host:port/db)"
config_schema:
  properties:
    default_table:
      type: string
      label: "Default Table"
      description: "Default database table for queries"
      placeholder: "users"
      group: defaults
    default_schema:
      type: string
      label: "Default Schema"
      description: "Database schema to query"
      placeholder: "public"
      default: "public"
      group: defaults
    result_limit:
      type: number
      label: "Default Result Limit"
      description: "Maximum rows to return by default"
      default: 50
      group: defaults
    allowed_tables:
      type: text
      label: "Allowed Tables"
      description: "Tables the agent is allowed to query (one per line, empty = all)"
      placeholder: "users\norders\nproducts\ninvoices"
      group: rules
    blocked_tables:
      type: text
      label: "Blocked Tables"
      description: "Tables the agent must never query (one per line)"
      placeholder: "audit_logs\npassword_resets\nsessions"
      group: rules
    blocked_columns:
      type: text
      label: "Blocked Columns"
      description: "Columns to never include in SELECT queries (one per line)"
      placeholder: "password_hash\nssn\ncredit_card\napi_secret"
      group: rules
    query_rules:
      type: text
      label: "Query Rules"
      description: "Rules and constraints for SQL queries"
      placeholder: "- Only SELECT queries allowed (enforced)\n- Always include LIMIT clause\n- Always include WHERE clause for large tables\n- Use created_at DESC for default ordering"
      group: rules
    query_template:
      type: text
      label: "Query Template"
      description: "Template for building SQL queries"
      placeholder: "SELECT {columns}\nFROM {table}\nWHERE {conditions}\nORDER BY created_at DESC\nLIMIT {limit}"
      group: templates
    response_template:
      type: text
      label: "Response Template"
      description: "Template for formatting query results"
      placeholder: "Found {count} records in {table}:\n{results}\n\nQuery: {sql}"
      group: templates
tool_schema:
  name: retool
  description: "Query Retool databases (read-only) — run SELECT queries and list tables"
  parameters:
    type: object
    properties:
      action:
        type: "string"
        description: "Which operation to perform"
        enum: ['query_db', 'list_tables']
      sql:
        type: "string"
        description: "SQL SELECT query for query_db"
        default: ""
    required: [action]
---
# Retool (Read-Only)
Query Retool databases with read-only access.

## Database Operations
- **query_db** — Execute a SELECT query against your Retool Database. Provide `sql` with a SELECT statement.
- **list_tables** — List all tables in the public schema.

## Safety
- Only SELECT queries are allowed — writes are blocked at the connection level.
- Always respect the allowed/blocked tables and columns configuration.
