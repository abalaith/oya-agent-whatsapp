import os
import json
import httpx
from datetime import datetime, timedelta

BASE = "https://api.github.com"


def get_headers():
    token = os.environ.get("GITHUB_TOKEN", "")
    return {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github+json",
        "User-Agent": "Oya/1.0",
    }


def api_get(headers, path, params=None, timeout=15):
    with httpx.Client(timeout=timeout) as c:
        r = c.get(f"{BASE}/{path}", headers=headers, params=params)
        r.raise_for_status()
        return r.json()


def api_post(headers, path, json_body, timeout=15):
    with httpx.Client(timeout=timeout) as c:
        r = c.post(f"{BASE}/{path}", headers=headers, json=json_body)
        r.raise_for_status()
        return r.json()


def format_repo(repo):
    description = repo.get("description", "") or ""
    if len(description) > 300:
        description = description[:300] + "..."
    return {
        "name": repo.get("name", ""),
        "full_name": repo.get("full_name", ""),
        "description": description,
        "stars": repo.get("stargazers_count", 0),
        "forks": repo.get("forks_count", 0),
        "language": repo.get("language", ""),
        "url": repo.get("html_url", ""),
        "updated_at": repo.get("updated_at", ""),
    }


def format_issue(item):
    body = item.get("body", "") or ""
    if len(body) > 300:
        body = body[:300] + "..."
    repo_url = item.get("repository_url", "")
    repo_name = "/".join(repo_url.split("/")[-2:]) if repo_url else ""
    return {
        "title": item.get("title", ""),
        "repo": repo_name,
        "state": item.get("state", ""),
        "author": (item.get("user") or {}).get("login", ""),
        "comments": item.get("comments", 0),
        "url": item.get("html_url", ""),
        "created_at": item.get("created_at", ""),
        "body": body,
    }


# --- Actions ---


def do_search_repos(headers, query, sort, limit, language):
    if not query:
        return {"error": "query is required for search_repos"}
    q = query
    if language:
        q += f"+language:{language}"
    valid_sorts = ["stars", "forks", "updated"]
    if sort not in valid_sorts:
        sort = "stars"
    data = api_get(headers, "search/repositories", params={"q": q, "sort": sort, "per_page": limit})
    repos = [format_repo(r) for r in data.get("items", [])]
    return {"query": query, "sort": sort, "language": language or "any", "repos": repos, "count": len(repos)}


def do_trending(headers, limit, language):
    week_ago = (datetime.utcnow() - timedelta(days=7)).strftime("%Y-%m-%d")
    q = f"created:>{week_ago}"
    if language:
        q += f"+language:{language}"
    data = api_get(headers, "search/repositories", params={"q": q, "sort": "stars", "per_page": limit})
    repos = [format_repo(r) for r in data.get("items", [])]
    return {"sort": "trending", "since": week_ago, "language": language or "any", "repos": repos, "count": len(repos)}


def do_get_repo(headers, repo):
    if not repo or "/" not in repo:
        return {"error": "repo is required in owner/name format for get_repo"}
    data = api_get(headers, f"repos/{repo}")
    description = data.get("description", "") or ""
    if len(description) > 500:
        description = description[:500] + "..."
    return {
        "name": data.get("name", ""),
        "full_name": data.get("full_name", ""),
        "description": description,
        "stars": data.get("stargazers_count", 0),
        "forks": data.get("forks_count", 0),
        "open_issues": data.get("open_issues_count", 0),
        "language": data.get("language", ""),
        "license": (data.get("license") or {}).get("spdx_id", ""),
        "topics": data.get("topics", []),
        "url": data.get("html_url", ""),
        "created_at": data.get("created_at", ""),
        "updated_at": data.get("updated_at", ""),
        "default_branch": data.get("default_branch", ""),
    }


def do_search_issues(headers, query, limit):
    if not query:
        return {"error": "query is required for search_issues"}
    data = api_get(headers, "search/issues", params={"q": f"{query}+type:issue", "per_page": limit})
    issues = [format_issue(i) for i in data.get("items", [])]
    return {"query": query, "issues": issues, "count": len(issues)}


def do_get_discussions(headers, repo, limit):
    if not repo or "/" not in repo:
        return {"error": "repo is required in owner/name format for get_discussions"}
    owner, name = repo.split("/", 1)
    query = """
    query($owner: String!, $name: String!, $first: Int!) {
      repository(owner: $owner, name: $name) {
        discussions(first: $first, orderBy: {field: CREATED_AT, direction: DESC}) {
          nodes {
            number
            title
            author { login }
            bodyText
            createdAt
            url
            id
          }
        }
      }
    }
    """
    variables = {"owner": owner, "name": name, "first": limit}
    data = api_post(headers, "graphql", {"query": query, "variables": variables})
    errors = data.get("errors")
    if errors:
        msg = errors[0].get("message", str(errors))
        return {"error": f"GraphQL error: {msg}. Ensure your token has discussion read permissions."}
    nodes = (data.get("data") or {}).get("repository", {}).get("discussions", {}).get("nodes", [])
    discussions = []
    for n in nodes:
        body = n.get("bodyText", "") or ""
        if len(body) > 300:
            body = body[:300] + "..."
        discussions.append({
            "number": n.get("number", 0),
            "title": n.get("title", ""),
            "author": (n.get("author") or {}).get("login", ""),
            "body": body,
            "url": n.get("url", ""),
            "created_at": n.get("createdAt", ""),
            "node_id": n.get("id", ""),
        })
    return {"repo": repo, "discussions": discussions, "count": len(discussions)}


def do_create_discussion_comment(headers, repo, discussion_number, comment_body, limit):
    if not repo or "/" not in repo:
        return {"error": "repo is required in owner/name format for create_discussion_comment"}
    if not discussion_number:
        return {"error": "discussion_number is required for create_discussion_comment"}
    if not comment_body:
        return {"error": "comment_body is required for create_discussion_comment"}

    # First, get the discussion node_id
    owner, name = repo.split("/", 1)
    id_query = """
    query($owner: String!, $name: String!, $number: Int!) {
      repository(owner: $owner, name: $name) {
        discussion(number: $number) {
          id
          title
        }
      }
    }
    """
    id_variables = {"owner": owner, "name": name, "number": discussion_number}
    id_data = api_post(headers, "graphql", {"query": id_query, "variables": id_variables})
    errors = id_data.get("errors")
    if errors:
        msg = errors[0].get("message", str(errors))
        return {"error": f"GraphQL error: {msg}. Ensure your token has discussion read permissions."}
    discussion = (id_data.get("data") or {}).get("repository", {}).get("discussion")
    if not discussion:
        return {"error": f"Discussion #{discussion_number} not found in {repo}"}
    discussion_id = discussion["id"]

    # Create the comment
    mutation = """
    mutation($discussionId: ID!, $body: String!) {
      addDiscussionComment(input: {discussionId: $discussionId, body: $body}) {
        comment {
          url
          createdAt
          author { login }
        }
      }
    }
    """
    mut_variables = {"discussionId": discussion_id, "body": comment_body}
    mut_data = api_post(headers, "graphql", {"query": mutation, "variables": mut_variables})
    errors = mut_data.get("errors")
    if errors:
        msg = errors[0].get("message", str(errors))
        return {"error": f"GraphQL error: {msg}. Ensure your token has discussion write permissions."}
    comment = (mut_data.get("data") or {}).get("addDiscussionComment", {}).get("comment", {})
    return {
        "success": True,
        "discussion": discussion.get("title", ""),
        "comment_url": comment.get("url", ""),
        "created_at": comment.get("createdAt", ""),
        "author": (comment.get("author") or {}).get("login", ""),
    }


# --- Main ---

try:
    headers = get_headers()
    token = os.environ.get("GITHUB_TOKEN", "")
    if not token:
        raise ValueError("No GitHub token available. Please provide a GITHUB_TOKEN in the skill resource settings.")
    inp = json.loads(os.environ.get("INPUT_JSON", "{}"))
    action = inp.get("action", "")
    limit = max(1, min(100, int(inp.get("limit", 10) or 10)))

    if action == "search_repos":
        query = inp.get("query", "").strip()
        sort = inp.get("sort", "stars") or "stars"
        language = inp.get("language", "").strip()
        result = do_search_repos(headers, query, sort, limit, language)
    elif action == "trending":
        language = inp.get("language", "").strip()
        result = do_trending(headers, limit, language)
    elif action == "get_repo":
        repo = inp.get("repo", "").strip()
        result = do_get_repo(headers, repo)
    elif action == "search_issues":
        query = inp.get("query", "").strip()
        result = do_search_issues(headers, query, limit)
    elif action == "get_discussions":
        repo = inp.get("repo", "").strip()
        result = do_get_discussions(headers, repo, limit)
    elif action == "create_discussion_comment":
        repo = inp.get("repo", "").strip()
        discussion_number = int(inp.get("discussion_number", 0) or 0)
        comment_body = inp.get("comment_body", "").strip()
        result = do_create_discussion_comment(headers, repo, discussion_number, comment_body, limit)
    else:
        result = {"error": f"Unknown action: {action}. Available: search_repos, trending, get_repo, search_issues, get_discussions, create_discussion_comment"}

    print(json.dumps(result))

except httpx.HTTPStatusError as e:
    status = e.response.status_code
    detail = ""
    try:
        detail = e.response.json().get("message", "") or str(e.response.json())
    except Exception:
        detail = e.response.text[:200]
    print(json.dumps({"error": f"GitHub API error {status}: {detail}" if detail else f"GitHub API error {status}"}))
except Exception as e:
    print(json.dumps({"error": str(e)}))
