import datetime
import hashlib
import json
import pathlib
import urllib.request

USERNAME = "aajadv3rma"
START_MARKER = "<!-- LIVE-DEV-DASHBOARD:START -->"
END_MARKER = "<!-- LIVE-DEV-DASHBOARD:END -->"
HEADERS = {"User-Agent": "aajadv3rma-profile-dashboard"}

def fetch_repos():
    url = f"https://api.github.com/users/{USERNAME}/repos?sort=updated&per_page=10"
    req = urllib.request.Request(url, headers=HEADERS)
    with urllib.request.urlopen(req, timeout=20) as resp:
        repos = json.loads(resp.read().decode("utf-8"))
    rows = []
    for r in repos:
        name = r.get("name", "")
        if r.get("fork") or name in (USERNAME, "daily-dsa-java"):
            continue
        desc = (r.get("description") or "Active project").replace("|", "-")
        lang = r.get("language") or "Multi"
        stars = r.get("stargazers_count", 0)
        updated = (r.get("pushed_at") or r.get("updated_at") or "")[:10]
        rows.append(f"| [{name}]({r['html_url']}) | {desc} | `{lang}` | {stars} | {updated} |")
    return rows[:6]

def fetch_daily_challenge(today):
    try:
        query = {
            "query": """
            query questionOfToday {
              activeDailyCodingChallengeQuestion {
                link
                question {
                  questionFrontendId
                  title
                  difficulty
                  topicTags { name }
                }
              }
            }
            """
        }
        req = urllib.request.Request(
            "https://leetcode.com/graphql",
            data=json.dumps(query).encode("utf-8"),
            headers={**HEADERS, "Content-Type": "application/json"},
        )
        with urllib.request.urlopen(req, timeout=20) as resp:
            data = json.loads(resp.read().decode("utf-8"))
        item = data["data"]["activeDailyCodingChallengeQuestion"]
        q = item["question"]
        tags = ", ".join(t["name"] for t in (q.get("topicTags") or [])[:4]) or "Algorithms"
        return {
            "source": "LeetCode Daily",
            "title": f"{q['questionFrontendId']}. {q['title']}",
            "difficulty": q["difficulty"],
            "tags": tags,
            "url": "https://leetcode.com" + item["link"],
        }
    except Exception:
        req = urllib.request.Request("https://codeforces.com/api/problemset.problems", headers=HEADERS)
        with urllib.request.urlopen(req, timeout=25) as resp:
            data = json.loads(resp.read().decode("utf-8"))
        problems = [p for p in data["result"]["problems"] if 800 <= p.get("rating", 0) <= 1500 and p.get("tags")]
        idx = int(hashlib.sha256(today.encode()).hexdigest(), 16) % len(problems)
        p = problems[idx]
        cid, pindex = p["contestId"], p["index"]
        return {
            "source": "Codeforces DSA",
            "title": f"{cid}{pindex}. {p['name']}",
            "difficulty": f"Rating {p.get('rating', 'N/A')}",
            "tags": ", ".join(p.get("tags", [])[:4]),
            "url": f"https://codeforces.com/problemset/problem/{cid}/{pindex}",
        }

def main():
    ist_now = datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=5, minutes=30)))
    today = ist_now.strftime("%Y-%m-%d")
    time_label = ist_now.strftime("%d %b %Y, %I:%M %p IST")

    repo_rows = fetch_repos()
    challenge = fetch_daily_challenge(today)

    table = "\n".join(repo_rows) if repo_rows else "| — | No public repositories found | — | — | — |"
    section = (
        f"{START_MARKER}\n"
        f"## Active Projects Snapshot\n\n"
        f"| Project | Description | Stack | Stars | Last Push |\n"
        f"| :--- | :--- | :--- | :---: | :---: |\n"
        f"{table}\n\n"
        f"### Daily Coding Challenge ({today})\n"
        f"- **Problem:** [{challenge['title']}]({challenge['url']}) ({challenge['source']})\n"
        f"- **Difficulty:** `{challenge['difficulty']}` · **Topics:** {challenge['tags']}\n\n"
        f"_Last synced: {time_label}_\n"
        f"{END_MARKER}"
    )

    readme_path = pathlib.Path("README.md")
    content = readme_path.read_text(encoding="utf-8") if readme_path.exists() else f"# Hi, I'm Aajad Verma\n"

    if START_MARKER in content and END_MARKER in content:
        before = content.split(START_MARKER)[0]
        after = content.split(END_MARKER)[1]
        updated = before + section + after
    else:
        updated = content.rstrip() + "\n\n" + section + "\n"

    readme_path.write_text(updated, encoding="utf-8")
    msg = f"docs(profile): sync active projects & daily challenge ({today})"
    pathlib.Path(".commit_msg.txt").write_text(msg, encoding="utf-8")
    print(msg)

if __name__ == "__main__":
    main()
