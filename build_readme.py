import json
import os
import re
import requests

USERNAME = "VTongTV"
TOKEN = os.environ.get("GITHUB_TOKEN", "")
README_PATH = "README.md"

def fetch_recent_repos():
    headers = {"Authorization": f"token {TOKEN}"} if TOKEN else {}
    repos = []
    page = 1
    while len(repos) < 100:
        r = requests.get(
            f"https://api.github.com/users/{USERNAME}/repos",
            headers=headers,
            params={"sort": "updated", "per_page": 100, "page": page},
            timeout=30,
        )
        if r.status_code != 200:
            break
        batch = r.json()
        if not batch:
            break
        for repo in batch:
            if repo.get("fork"):
                continue
            if "-from-scratch" in repo["name"] or "-scratch" in repo["name"]:
                continue
            repos.append({
                "name": repo["name"],
                "desc": repo.get("description", "") or "",
                "url": repo["html_url"],
                "lang": repo.get("language", ""),
                "stars": repo.get("stargazers_count", 0),
                "updated": repo.get("pushed_at", ""),
            })
        page += 1
    repos.sort(key=lambda r: r["updated"], reverse=True)
    return repos[:5]

def build_repos_markdown(repos):
    if not repos:
        return "<!-- no data yet -->"
    lines = []
    for r in repos:
        desc = r["desc"][:80] + "..." if len(r["desc"]) > 80 else r["desc"]
        lang = f"`{r['lang']}`" if r["lang"] else ""
        lines.append(f"- [{r['name']}]({r['url']}) {lang} -- {desc}")
    return "\n".join(lines)

def replace_section(content, start_marker, end_marker, new_body):
    pattern = re.compile(
        rf"{re.escape(start_marker)}.*?{re.escape(end_marker)}",
        re.DOTALL,
    )
    replacement = f"{start_marker}\n{new_body}\n{end_marker}"
    return pattern.sub(replacement, content)

def main():
    repos = fetch_recent_repos()
    repos_md = build_repos_markdown(repos)

    with open(README_PATH, "r", encoding="utf-8") as f:
        content = f.read()

    updated = replace_section(
        content,
        "<!-- RECENT-REPOS:START -->",
        "<!-- RECENT-REPOS:END -->",
        repos_md,
    )

    if updated != content:
        with open(README_PATH, "w", encoding="utf-8") as f:
            f.write(updated)
        print("README updated")
    else:
        print("No changes")

if __name__ == "__main__":
    main()
