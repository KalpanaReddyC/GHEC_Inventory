"""Run inventory for a single organization."""
import os
import time
import logging
from dotenv import load_dotenv
from github_inventory import PATManager, GitHubInventoryCollector

load_dotenv()

ORG_LOGIN = "im-sandbox-rushik"

pats = [p.strip() for p in os.getenv("GITHUB_PATS").split(",") if p.strip()]
pm = PATManager(pats)
c = GitHubInventoryCollector(
    enterprise_name=os.getenv("GITHUB_ENTERPRISE_NAME"),
    pat_manager=pm,
    graphql_url=os.getenv("GITHUB_GRAPHQL_URL", "https://api.github.com/graphql"),
    api_url=os.getenv("GITHUB_API_URL", "https://api.github.com"),
    repo_csv_file="github_inventory_repositories.csv",
    org_csv_file="github_inventory_organizations.csv",
)
c.initialize_repo_csv()
c.initialize_org_csv()

org_webhooks = c.get_organization_webhooks(ORG_LOGIN)
org_apps = c.get_organization_apps(ORG_LOGIN)
org_teams = c.get_organization_teams(ORG_LOGIN)
org_runners_self, org_runners_github = c.get_organization_runners(ORG_LOGIN)
repos = c.get_organization_repositories(ORG_LOGIN)

org_stats = {
    "total_repos": 0, "private_repos": 0, "public_repos": 0,
    "internal_repos": 0, "archived_repos": 0, "fork_repos": 0,
}

for idx, repo in enumerate(repos, 1):
    print(f"\n[{idx}/{len(repos)}] Processing: {repo['nameWithOwner']}")
    owner, repo_name = repo["nameWithOwner"].split("/")

    wf = c.get_repository_workflows(owner, repo_name)
    wh = c.get_repository_webhooks(owner, repo_name)
    apps = c.get_installed_apps(owner, repo_name)
    sz = c.get_repository_size(owner, repo_name)
    rn = c.get_repository_runners(owner, repo_name)
    lfs = c.get_repository_lfs_usage(owner, repo_name)
    default_branch = repo["defaultBranchRef"]["name"] if repo.get("defaultBranchRef") else ""
    commits = c.get_repository_commit_count(owner, repo_name, default_branch)

    rec = {
        "Organization": ORG_LOGIN,
        "Repository": repo["name"],
        "Description": repo.get("description", ""),
        "URL": repo["url"],
        "Is_Private": repo.get("visibility", "PRIVATE") == "PRIVATE",
        "Is_Internal": repo.get("visibility", "PRIVATE") == "INTERNAL",
        "Is_Public": repo.get("visibility", "PRIVATE") == "PUBLIC",
        "Is_Fork": repo["isFork"],
        "Is_Archived": repo["isArchived"],
        "Created_At": repo["createdAt"],
        "Updated_At": repo["updatedAt"],
        "Pushed_At": repo.get("pushedAt", ""),
        "Size_KB": sz,
        "Default_Branch": default_branch,
        "Forks": repo.get("forkCount", 0),
        "Open_Issues": repo["issues"]["totalCount"] if repo.get("issues") else 0,
        "Pull_Requests": repo["pullRequests"]["totalCount"] if repo.get("pullRequests") else 0,
        "Releases": repo["releases"]["totalCount"] if repo.get("releases") else 0,
        "Branches": repo["branches"]["totalCount"] if repo.get("branches") else 0,
        "Tags": repo["tags"]["totalCount"] if repo.get("tags") else 0,
        "Workflows": wf,
        "Repo_Webhooks": wh,
        "Repo_Runners": rn,
        "GitHub_Apps": apps,
        "LFS_Files": lfs,
        "Commits": commits,
    }
    c.inventory_data.append(rec)
    c.append_repo_to_csv(rec)

    vis = repo.get("visibility", "PRIVATE")
    org_stats["total_repos"] += 1
    org_stats["private_repos"] += 1 if vis == "PRIVATE" else 0
    org_stats["public_repos"] += 1 if vis == "PUBLIC" else 0
    org_stats["internal_repos"] += 1 if vis == "INTERNAL" else 0
    org_stats["archived_repos"] += 1 if repo["isArchived"] else 0
    org_stats["fork_repos"] += 1 if repo["isFork"] else 0

    if wf > 0:
        print(f"  [OK] Workflows: {wf}")
    if wh > 0:
        print(f"  [OK] Webhooks: {wh}")
    if lfs:
        print(f"  [OK] LFS: {lfs}")

    time.sleep(0.3)

org_sum = {
    "Organization": ORG_LOGIN, "Description": "", "URL": f"https://github.com/{ORG_LOGIN}",
    "Created_At": "", "Total_Repositories": org_stats["total_repos"],
    "Private_Repositories": org_stats["private_repos"],
    "Public_Repositories": org_stats["public_repos"],
    "Internal_Repositories": org_stats["internal_repos"],
    "Archived_Repositories": org_stats["archived_repos"],
    "Fork_Repositories": org_stats["fork_repos"],
    "Org_Webhooks": org_webhooks, "Org_GitHub_Apps": org_apps, "Org_Teams": org_teams,
    "Org_Runners_SelfHosted": org_runners_self, "Org_Runners_GitHubHosted": org_runners_github,
}
c.append_org_to_csv(org_sum)
c.print_summary()
print("\nDone! CSVs saved to output/ folder.")
