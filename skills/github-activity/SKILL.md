---
name: github-activity
display_name: "GitHub"
description: "Search GitHub repos, trending projects, issues, and discussions"
category: social
icon: code
skill_type: sandbox
catalog_type: addon
requirements: "httpx>=0.25"
resource_requirements:
  - env_var: GITHUB_TOKEN
    name: "GitHub Personal Access Token"
    description: "PAT with repo and discussion scopes — generate at github.com/settings/tokens"
tool_schema:
  name: github_activity
  description: "Search GitHub repos, trending projects, issues, and discussions"
  parameters:
    type: object
    properties:
      action:
        type: "string"
        description: "Which operation to perform"
        enum: ['search_repos', 'trending', 'get_repo', 'search_issues', 'get_discussions', 'create_discussion_comment']
      query:
        type: "string"
        description: "Search query -- for search_repos, search_issues"
        default: ""
      repo:
        type: "string"
        description: "Repository in owner/name format -- for get_repo, get_discussions, create_discussion_comment"
        default: ""
      discussion_number:
        type: "integer"
        description: "Discussion number -- for create_discussion_comment"
        default: 0
      comment_body:
        type: "string"
        description: "Comment text -- for create_discussion_comment"
        default: ""
      sort:
        type: "string"
        description: "Sort order for search_repos: stars, forks, or updated (default stars)"
        default: "stars"
      limit:
        type: "integer"
        description: "Number of results to return (default 10)"
        default: 10
      language:
        type: "string"
        description: "Programming language filter -- for search_repos, trending"
        default: ""
    required: [action]
---
# GitHub

Search GitHub repositories, trending projects, issues, and discussions.

## Actions
- **search_repos** -- Search repositories by keyword, language, and sort order
- **trending** -- Find trending repos created in the last 7 days, sorted by stars
- **get_repo** -- Get details about a specific repository (owner/name format)
- **search_issues** -- Search issues across GitHub by keyword
- **get_discussions** -- List discussions in a repository
- **create_discussion_comment** -- Comment on a GitHub discussion

## Tips
- Use `trending` to discover what's hot in AI/ML this week
- Use `search_repos` with language filter to find projects in specific ecosystems
- Use `get_discussions` to find active conversations to engage with
