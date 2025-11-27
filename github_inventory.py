"""
GitHub Enterprise Inventory Script
Fetches comprehensive inventory details from a GitHub Enterprise using GraphQL API
Uses round-robin mechanism for multiple PATs to manage API rate limits
"""

import os
import csv
import sys
import time
import logging
from datetime import datetime
from typing import List, Dict, Any, Optional
import requests
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


class PATManager:
    """Manages multiple Personal Access Tokens with round-robin rotation"""

    def __init__(self, tokens: List[str]):
        if not tokens or all(not t.strip() for t in tokens):
            raise ValueError("At least one valid GitHub PAT is required")

        self.tokens = [t.strip() for t in tokens if t.strip()]
        self.current_index = 0
        self.rate_limit_info = {}

        logging.info(f"Initialized PAT Manager with {len(self.tokens)} token(s)")
        print(f"Initialized PAT Manager with {len(self.tokens)} token(s)")

    def get_next_token(self) -> str:
        """Get next token using round-robin mechanism"""
        token = self.tokens[self.current_index]
        self.current_index = (self.current_index + 1) % len(self.tokens)
        return token

    def get_current_token(self) -> str:
        """Get current token without rotating"""
        return self.tokens[self.current_index]

    def check_rate_limit(self, token: str, graphql_url: str) -> Dict[str, Any]:
        """Check rate limit for a specific token"""
        query = """
        query {
          rateLimit {
            limit
            cost
            remaining
            resetAt
          }
        }
        """

        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        }

        try:
            response = requests.post(
                graphql_url, json={"query": query}, headers=headers, timeout=30
            )

            if response.status_code == 200:
                data = response.json()
                if "data" in data and "rateLimit" in data["data"]:
                    return data["data"]["rateLimit"]
        except Exception as e:
            print(f"Warning: Could not check rate limit: {e}")

        return {"remaining": -1, "limit": -1}

    def wait_for_rate_limit_reset(self, token: str, graphql_url: str):
        """Wait if rate limit is exhausted"""
        rate_limit = self.check_rate_limit(token, graphql_url)

        if rate_limit["remaining"] < 100:  # Buffer of 100 requests
            logging.warning(
                f"Rate limit low (remaining: {rate_limit['remaining']}). Switching to next token..."
            )
            print(
                f"Rate limit low (remaining: {rate_limit['remaining']}). Switching to next token..."
            )
            return self.get_next_token()

        return token


class GitHubInventoryCollector:
    """Collects comprehensive inventory data from GitHub Enterprise"""

    def __init__(
        self,
        enterprise_name: str,
        pat_manager: PATManager,
        graphql_url: str,
        api_url: str,
        repo_csv_file: str,
        org_csv_file: str,
    ):
        self.enterprise_name = enterprise_name
        self.pat_manager = pat_manager
        self.graphql_url = graphql_url
        self.api_url = api_url

        # Create output directories
        os.makedirs("output", exist_ok=True)
        os.makedirs(os.path.join("output", "logs"), exist_ok=True)

        # Set file paths in output directory
        self.repo_csv_file = os.path.join("output", repo_csv_file)
        self.org_csv_file = os.path.join("output", org_csv_file)

        self.inventory_data = []
        self.org_summary_data = []
        self.repo_csv_initialized = False
        self.org_csv_initialized = False

    def execute_graphql_query(
        self, query: str, variables: Optional[Dict] = None
    ) -> Dict:
        """Execute GraphQL query with rate limit handling"""
        token = self.pat_manager.get_current_token()
        token = self.pat_manager.wait_for_rate_limit_reset(token, self.graphql_url)

        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        }

        payload = {"query": query}
        if variables:
            payload["variables"] = variables

        max_retries = 3
        for attempt in range(max_retries):
            try:
                response = requests.post(
                    self.graphql_url, json=payload, headers=headers, timeout=60
                )

                if response.status_code == 200:
                    data = response.json()
                    if "errors" in data:
                        # Check if errors are FORBIDDEN (persistent, don't retry)
                        has_forbidden = any(
                            err.get("type") == "FORBIDDEN"
                            for err in data.get("errors", [])
                        )
                        if has_forbidden:
                            # Only print once, don't retry FORBIDDEN errors
                            if attempt == 0:
                                forbidden_count = sum(
                                    1
                                    for err in data["errors"]
                                    if err.get("type") == "FORBIDDEN"
                                )
                                logging.warning(
                                    f"FORBIDDEN access detected for {forbidden_count} resource(s)"
                                )
                                print(
                                    f"[WARNING] {forbidden_count} organization(s) restricted due to PAT token lifetime requirements (>7 days)"
                                )
                            return data
                        else:
                            # Other errors - print and retry
                            print(f"GraphQL errors: {data['errors']}")
                            if attempt < max_retries - 1:
                                time.sleep(2**attempt)
                                continue
                    return data
                elif response.status_code == 403 or response.status_code == 429:
                    print(f"Rate limit hit, rotating token...")
                    token = self.pat_manager.get_next_token()
                    headers["Authorization"] = f"Bearer {token}"
                    time.sleep(5)
                else:
                    print(f"HTTP {response.status_code}: {response.text}")
                    if attempt < max_retries - 1:
                        time.sleep(2**attempt)

            except Exception as e:
                print(f"Request error (attempt {attempt + 1}/{max_retries}): {e}")
                if attempt < max_retries - 1:
                    time.sleep(2**attempt)

        return {}

    def get_enterprise_organizations(self) -> List[Dict]:
        """Fetch all organizations in the enterprise"""
        print("Fetching enterprise organizations...")

        query = """
        query($enterprise: String!, $cursor: String) {
          enterprise(slug: $enterprise) {
            organizations(first: 100, after: $cursor) {
              pageInfo {
                hasNextPage
                endCursor
              }
              nodes {
                login
                name
                description
                createdAt
                url
              }
            }
          }
        }
        """

        organizations = []
        has_next_page = True
        cursor = None

        while has_next_page:
            variables = {"enterprise": self.enterprise_name, "cursor": cursor}
            result = self.execute_graphql_query(query, variables)

            if "data" in result and result["data"] and "enterprise" in result["data"]:
                orgs_data = result["data"]["enterprise"]["organizations"]
                # Filter out None values (organizations with access restrictions)
                valid_orgs = [org for org in orgs_data["nodes"] if org is not None]
                organizations.extend(valid_orgs)

                has_next_page = orgs_data["pageInfo"]["hasNextPage"]
                cursor = orgs_data["pageInfo"]["endCursor"]
            else:
                break

        logging.info(
            f"Found {len(organizations)} organizations in enterprise '{self.enterprise_name}'"
        )
        print(f"Found {len(organizations)} organizations")
        print(f"Note: Some organizations may be skipped due to access restrictions")
        return organizations

    def get_organization_repositories(self, org_login: str) -> List[Dict]:
        """Fetch all repositories for an organization"""
        logging.info(f"Fetching repositories for organization: {org_login}")
        print(f"Fetching repositories for organization: {org_login}")

        query = """
        query($org: String!, $cursor: String) {
          organization(login: $org) {
            repositories(first: 100, after: $cursor) {
              pageInfo {
                hasNextPage
                endCursor
              }
              nodes {
                name
                nameWithOwner
                description
                url
                visibility
                isPrivate
                isFork
                isArchived
                createdAt
                updatedAt
                pushedAt
                defaultBranchRef {
                  name
                }
                forkCount
                issues {
                  totalCount
                }
                pullRequests {
                  totalCount
                }
                releases {
                  totalCount
                }
                branches: refs(refPrefix: "refs/heads/", first: 0) {
                  totalCount
                }
                tags: refs(refPrefix: "refs/tags/", first: 0) {
                  totalCount
                }
              }
            }
          }
        }
        """

        repositories = []
        has_next_page = True
        cursor = None

        while has_next_page:
            variables = {"org": org_login, "cursor": cursor}
            result = self.execute_graphql_query(query, variables)

            if "data" in result and result["data"] and "organization" in result["data"]:
                repos_data = result["data"]["organization"]["repositories"]
                repositories.extend(repos_data["nodes"])

                has_next_page = repos_data["pageInfo"]["hasNextPage"]
                cursor = repos_data["pageInfo"]["endCursor"]
            else:
                break

            time.sleep(0.5)  # Be nice to the API

        logging.info(f"Found {len(repositories)} repositories in {org_login}")
        print(f"Found {len(repositories)} repositories in {org_login}")
        return repositories

    def get_repository_workflows(self, owner: str, repo_name: str) -> int:
        """Get count of GitHub Actions workflows using REST API"""
        token = self.pat_manager.get_current_token()

        headers = {
            "Authorization": f"Bearer {token}",
            "Accept": "application/vnd.github+json",
        }

        url = f"{self.api_url}/repos/{owner}/{repo_name}/actions/workflows"

        try:
            response = requests.get(url, headers=headers, timeout=30)
            if response.status_code == 200:
                data = response.json()
                return data.get("total_count", 0)
            elif response.status_code == 404:
                return 0  # Actions not enabled
        except Exception as e:
            print(f"Error fetching workflows for {owner}/{repo_name}: {e}")

        return 0

    def get_repository_size(self, owner: str, repo_name: str) -> int:
        """Get repository size in KB using REST API (more reliable than GraphQL diskUsage)"""
        token = self.pat_manager.get_current_token()

        headers = {
            "Authorization": f"Bearer {token}",
            "Accept": "application/vnd.github+json",
        }

        url = f"{self.api_url}/repos/{owner}/{repo_name}"

        try:
            response = requests.get(url, headers=headers, timeout=30)
            if response.status_code == 200:
                data = response.json()
                return data.get("size", 0)  # Size in KB
        except Exception:
            pass

        return 0

    def get_repository_webhooks(self, owner: str, repo_name: str) -> int:
        """Get count of webhooks using REST API"""
        token = self.pat_manager.get_current_token()

        headers = {
            "Authorization": f"Bearer {token}",
            "Accept": "application/vnd.github+json",
        }

        url = f"{self.api_url}/repos/{owner}/{repo_name}/hooks"

        try:
            response = requests.get(url, headers=headers, timeout=30)
            if response.status_code == 200:
                hooks = response.json()
                return len(hooks)
        except Exception as e:
            print(f"Error fetching webhooks for {owner}/{repo_name}: {e}")

        return 0

    def get_organization_webhooks(self, org_login: str) -> int:
        """Get count of organization-level webhooks"""
        token = self.pat_manager.get_current_token()

        headers = {
            "Authorization": f"Bearer {token}",
            "Accept": "application/vnd.github+json",
        }

        url = f"{self.api_url}/orgs/{org_login}/hooks"

        try:
            response = requests.get(url, headers=headers, timeout=30)
            if response.status_code == 200:
                hooks = response.json()
                return len(hooks)
        except Exception as e:
            print(f"Error fetching org webhooks for {org_login}: {e}")

        return 0

    def get_installed_apps(self, owner: str, repo_name: str) -> int:
        """Get count of installed GitHub Apps for a repository"""
        token = self.pat_manager.get_current_token()

        headers = {
            "Authorization": f"Bearer {token}",
            "Accept": "application/vnd.github+json",
        }

        # Note: This requires additional permissions
        url = f"{self.api_url}/repos/{owner}/{repo_name}/installation"

        try:
            response = requests.get(url, headers=headers, timeout=30)
            if response.status_code == 200:
                return 1  # At least one app is installed
        except Exception:
            pass

        return 0

    def get_organization_apps(self, org_login: str) -> int:
        """Get count of installed GitHub Apps for an organization"""
        token = self.pat_manager.get_current_token()

        headers = {
            "Authorization": f"Bearer {token}",
            "Accept": "application/vnd.github+json",
        }

        url = f"{self.api_url}/orgs/{org_login}/installations"

        try:
            response = requests.get(url, headers=headers, timeout=30)
            if response.status_code == 200:
                data = response.json()
                # Return the total count of installed apps
                return data.get("total_count", 0)
            elif response.status_code == 404:
                # No installations endpoint or no apps
                return 0
        except Exception as e:
            print(f"  [WARNING] Could not fetch organization apps: {e}")
            pass

        return 0

    def get_organization_teams(self, org_login: str) -> int:
        """Get count of teams in an organization"""
        token = self.pat_manager.get_current_token()

        headers = {
            "Authorization": f"Bearer {token}",
            "Accept": "application/vnd.github+json",
        }

        url = f"{self.api_url}/orgs/{org_login}/teams"

        try:
            response = requests.get(url, headers=headers, timeout=30)
            if response.status_code == 200:
                teams = response.json()
                return len(teams)
            elif response.status_code == 404:
                return 0
        except Exception as e:
            print(f"  [WARNING] Could not fetch organization teams: {e}")
            pass

        return 0

    def get_organization_runners(self, org_login: str) -> int:
        """Get count of all runners (self-hosted and GitHub-hosted) in an organization

        Note: Requires 'admin:org' scope on the PAT to access runner information.
        If the API returns 0 but runners exist in the UI, check PAT permissions.
        """
        token = self.pat_manager.get_current_token()

        headers = {
            "Authorization": f"Bearer {token}",
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
        }

        self_hosted_count = 0
        github_hosted_count = 0

        # Get self-hosted runners
        url = f"{self.api_url}/orgs/{org_login}/actions/runners?per_page=100"
        try:
            response = requests.get(url, headers=headers, timeout=30)
            if response.status_code == 200:
                data = response.json()
                self_hosted_count = data.get("total_count", 0)
                if self_hosted_count > 0:
                    logging.info(
                        f"Organization {org_login} has {self_hosted_count} self-hosted runner(s)"
                    )
            elif response.status_code == 403:
                logging.warning(
                    f"Forbidden: PAT may need 'admin:org' scope to list self-hosted runners for {org_login}"
                )
        except Exception as e:
            logging.warning(f"Could not fetch self-hosted runners for {org_login}: {e}")

        # Get GitHub-hosted runners
        url = f"{self.api_url}/orgs/{org_login}/actions/hosted-runners?per_page=100"
        try:
            response = requests.get(url, headers=headers, timeout=30)
            if response.status_code == 200:
                data = response.json()
                github_hosted_count = data.get("total_count", 0)
                if github_hosted_count > 0:
                    logging.info(
                        f"Organization {org_login} has {github_hosted_count} GitHub-hosted runner(s)"
                    )
            elif response.status_code == 403:
                logging.warning(
                    f"Forbidden: PAT may need 'admin:org' scope to list GitHub-hosted runners for {org_login}"
                )
        except Exception as e:
            logging.warning(
                f"Could not fetch GitHub-hosted runners for {org_login}: {e}"
            )

        total_count = self_hosted_count + github_hosted_count
        if total_count > 0:
            print(
                f"  [OK] Runners: {total_count} (Self-hosted: {self_hosted_count}, GitHub-hosted: {github_hosted_count})"
            )
        return (self_hosted_count, github_hosted_count)

    def get_repository_runners(self, owner: str, repo_name: str) -> int:
        """Get count of all runners (self-hosted) for a repository

        Note: GitHub-hosted runners are not available at repository level,
        they are managed at organization level only.
        """
        token = self.pat_manager.get_current_token()

        headers = {
            "Authorization": f"Bearer {token}",
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
        }

        # Get self-hosted runners only (GitHub-hosted runners are org-level)
        url = f"{self.api_url}/repos/{owner}/{repo_name}/actions/runners?per_page=100"

        try:
            response = requests.get(url, headers=headers, timeout=30)
            if response.status_code == 200:
                data = response.json()
                total_count = data.get("total_count", 0)
                if total_count > 0:
                    logging.debug(
                        f"Repository {owner}/{repo_name} has {total_count} self-hosted runner(s)"
                    )
                return total_count
            elif response.status_code == 404:
                # Repository doesn't have actions enabled or no runners
                return 0
            else:
                logging.debug(
                    f"Status {response.status_code} fetching runners for {owner}/{repo_name}"
                )
                return 0
        except Exception:
            pass

        return 0

    def initialize_repo_csv(self):
        """Initialize repository CSV file with headers"""
        if self.repo_csv_initialized:
            return

        logging.info(f"Initializing repository CSV: {self.repo_csv_file}")

        fieldnames = [
            "Organization",
            "Repository",
            "Description",
            "URL",
            "Is_Private",
            "Is_Internal",
            "Is_Public",
            "Is_Fork",
            "Is_Archived",
            "Created_At",
            "Updated_At",
            "Pushed_At",
            "Size_KB",
            "Default_Branch",
            "Forks",
            "Open_Issues",
            "Pull_Requests",
            "Releases",
            "Branches",
            "Tags",
            "Workflows",
            "Repo_Webhooks",
            "Repo_Runners",
            "GitHub_Apps",
        ]

        with open(self.repo_csv_file, "w", newline="", encoding="utf-8") as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()

        self.repo_csv_initialized = True
        print(f"[OK] Initialized repository CSV: {self.repo_csv_file}")

    def initialize_org_csv(self):
        """Initialize organization CSV file with headers"""
        if self.org_csv_initialized:
            return

        logging.info(f"Initializing organization CSV: {self.org_csv_file}")

        fieldnames = [
            "Organization",
            "Description",
            "URL",
            "Created_At",
            "Total_Repositories",
            "Private_Repositories",
            "Public_Repositories",
            "Internal_Repositories",
            "Archived_Repositories",
            "Fork_Repositories",
            "Org_Webhooks",
            "Org_GitHub_Apps",
            "Org_Teams",
            "Org_Runners_SelfHosted",
            "Org_Runners_GitHubHosted",
        ]

        with open(self.org_csv_file, "w", newline="", encoding="utf-8") as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()

        self.org_csv_initialized = True
        print(f"[OK] Initialized organization CSV: {self.org_csv_file}")

    def append_repo_to_csv(self, repo_data: Dict):
        """Append a single repository record to CSV"""
        fieldnames = [
            "Organization",
            "Repository",
            "Description",
            "URL",
            "Is_Private",
            "Is_Internal",
            "Is_Public",
            "Is_Fork",
            "Is_Archived",
            "Created_At",
            "Updated_At",
            "Pushed_At",
            "Size_KB",
            "Default_Branch",
            "Forks",
            "Open_Issues",
            "Pull_Requests",
            "Releases",
            "Branches",
            "Tags",
            "Workflows",
            "Repo_Webhooks",
            "Repo_Runners",
            "GitHub_Apps",
        ]

        with open(self.repo_csv_file, "a", newline="", encoding="utf-8") as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writerow(repo_data)

    def append_org_to_csv(self, org_data: Dict):
        """Append a single organization summary to CSV"""
        fieldnames = [
            "Organization",
            "Description",
            "URL",
            "Created_At",
            "Total_Repositories",
            "Private_Repositories",
            "Public_Repositories",
            "Internal_Repositories",
            "Archived_Repositories",
            "Fork_Repositories",
            "Org_Webhooks",
            "Org_GitHub_Apps",
            "Org_Teams",
            "Org_Runners_SelfHosted",
            "Org_Runners_GitHubHosted",
        ]

        with open(self.org_csv_file, "a", newline="", encoding="utf-8") as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writerow(org_data)

    def collect_inventory(self):
        """Main method to collect all inventory data"""
        logging.info(
            f"Starting inventory collection for enterprise: {self.enterprise_name}"
        )
        print(f"\n{'='*60}")
        print(f"Starting GitHub Enterprise Inventory Collection")
        print(f"Enterprise: {self.enterprise_name}")
        print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"{'='*60}\n")

        # Initialize CSV files
        self.initialize_repo_csv()
        self.initialize_org_csv()

        # Get all organizations
        organizations = self.get_enterprise_organizations()

        if not organizations:
            print("No organizations found or unable to access enterprise data.")
            print("Please check:")
            print("1. Enterprise name is correct")
            print("2. PATs have 'admin:enterprise' scope")
            print("3. You have access to the enterprise")
            return

        # Limit organizations if MAX_ORGS_TO_PROCESS is set
        max_orgs = os.getenv("MAX_ORGS_TO_PROCESS", "0")
        try:
            max_orgs_int = int(max_orgs)
            if max_orgs_int > 0:
                organizations = organizations[:max_orgs_int]
                logging.warning(
                    f"Testing mode: Processing only first {max_orgs_int} organizations"
                )
                print(
                    f"\n[WARNING]  Testing mode: Processing only first {max_orgs_int} organizations\n"
                )
        except ValueError:
            pass  # If not a valid number, process all

        total_orgs = len(organizations)
        logging.info(f"Processing {total_orgs} organization(s)")

        # Process each organization
        for idx, org in enumerate(organizations, 1):
            try:
                # Skip if org is None (shouldn't happen after filtering, but safety check)
                if org is None:
                    logging.warning("Skipping None organization entry")
                    print(f"\\nSkipping None organization entry")
                    continue

                org_login = org["login"]
                logging.info(f"Processing organization {idx}/{total_orgs}: {org_login}")
                print(f"\\n{'='*60}")
                print(f"Processing Organization: {org_login}")
                print(f"{'='*60}")

                # Get org-level webhooks, GitHub Apps, and teams
                org_webhooks = self.get_organization_webhooks(org_login)
                org_apps = self.get_organization_apps(org_login)
                org_teams = self.get_organization_teams(org_login)
                org_runners_self, org_runners_github = self.get_organization_runners(
                    org_login
                )

                # Get repositories
                repositories = self.get_organization_repositories(org_login)

                # Initialize org-level statistics
                org_stats = {
                    "total_repos": 0,
                    "private_repos": 0,
                    "public_repos": 0,
                    "internal_repos": 0,
                    "archived_repos": 0,
                    "fork_repos": 0,
                }

                # Process each repository
                for idx, repo in enumerate(repositories, 1):
                    print(
                        f"\\n[{idx}/{len(repositories)}] Processing: {repo['nameWithOwner']}"
                    )

                    owner_repo = repo["nameWithOwner"].split("/")
                    owner = owner_repo[0]
                    repo_name = owner_repo[1]

                    # Fetch additional metadata
                    workflows_count = self.get_repository_workflows(owner, repo_name)
                    webhooks_count = self.get_repository_webhooks(owner, repo_name)
                    apps_count = self.get_installed_apps(owner, repo_name)
                    repo_size = self.get_repository_size(owner, repo_name)
                    runners_count = self.get_repository_runners(owner, repo_name)

                    # Compile inventory record
                    inventory_record = {
                        "Organization": org_login,
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
                        "Size_KB": repo_size,
                        "Default_Branch": (
                            repo["defaultBranchRef"]["name"]
                            if repo.get("defaultBranchRef")
                            else ""
                        ),
                        "Forks": repo.get("forkCount", 0),
                        "Open_Issues": (
                            repo["issues"]["totalCount"] if repo.get("issues") else 0
                        ),
                        "Pull_Requests": (
                            repo["pullRequests"]["totalCount"]
                            if repo.get("pullRequests")
                            else 0
                        ),
                        "Releases": (
                            repo["releases"]["totalCount"]
                            if repo.get("releases")
                            else 0
                        ),
                        "Branches": (
                            repo["branches"]["totalCount"]
                            if repo.get("branches")
                            else 0
                        ),
                        "Tags": repo["tags"]["totalCount"] if repo.get("tags") else 0,
                        "Workflows": workflows_count,
                        "Repo_Webhooks": webhooks_count,
                        "Repo_Runners": runners_count,
                        "GitHub_Apps": apps_count,
                    }

                    # Append to in-memory list and write to CSV immediately
                    self.inventory_data.append(inventory_record)
                    self.append_repo_to_csv(inventory_record)

                    # Update org-level statistics
                    org_stats["total_repos"] += 1
                    visibility = repo.get("visibility", "PRIVATE")
                    org_stats["private_repos"] += 1 if visibility == "PRIVATE" else 0
                    org_stats["public_repos"] += 1 if visibility == "PUBLIC" else 0
                    org_stats["internal_repos"] += 1 if visibility == "INTERNAL" else 0
                    org_stats["archived_repos"] += 1 if repo["isArchived"] else 0
                    org_stats["fork_repos"] += 1 if repo["isFork"] else 0

                    # Progress indicator
                    if workflows_count > 0:
                        print(f"  [OK] Workflows: {workflows_count}")
                    if webhooks_count > 0:
                        print(f"  [OK] Webhooks: {webhooks_count}")
                    if repo["branches"]["totalCount"] > 1:
                        print(f"  [OK] Branches: {repo['branches']['totalCount']}")

                    time.sleep(0.3)  # Rate limiting courtesy

                # Write organization summary to CSV (after processing all repos)
                org_summary = {
                    "Organization": org_login,
                    "Description": org.get("description", ""),
                    "URL": org["url"],
                    "Created_At": org["createdAt"],
                    "Total_Repositories": org_stats["total_repos"],
                    "Private_Repositories": org_stats["private_repos"],
                    "Public_Repositories": org_stats["public_repos"],
                    "Internal_Repositories": org_stats["internal_repos"],
                    "Archived_Repositories": org_stats["archived_repos"],
                    "Fork_Repositories": org_stats["fork_repos"],
                    "Org_Webhooks": org_webhooks,
                    "Org_GitHub_Apps": org_apps,
                    "Org_Teams": org_teams,
                    "Org_Runners_SelfHosted": org_runners_self,
                    "Org_Runners_GitHubHosted": org_runners_github,
                }

                self.org_summary_data.append(org_summary)
                self.append_org_to_csv(org_summary)

                logging.info(
                    f"Completed organization {org_login}: {org_stats['total_repos']} repositories, {org_webhooks} webhooks, {org_apps} apps, {org_teams} teams, {org_runners_self + org_runners_github} runners (self-hosted: {org_runners_self}, GitHub-hosted: {org_runners_github})"
                )
                print(
                    f"\n[OK] Completed organization {org_login}: {org_stats['total_repos']} repositories processed"
                )

            except Exception as e:
                logging.error(
                    f"Error processing organization {org.get('login', 'Unknown')}: {e}"
                )
                print(
                    f"\\n\u2717 Error processing organization {org.get('login', 'Unknown')}: {e}"
                )
                print(f"Skipping this organization and continuing with the next one...")
                continue

        logging.info(
            f"Inventory collection complete: {len(self.inventory_data)} repositories, {len(self.org_summary_data)} organizations"
        )
        print(f"\\n{'='*60}")
        print(f"Inventory collection complete!")
        print(f"Total repositories processed: {len(self.inventory_data)}")
        print(f"Total organizations processed: {len(self.org_summary_data)}")
        print(f"{'='*60}\\n")

    def export_to_csv(self, filename: str):
        """Export inventory data to CSV"""
        if not self.inventory_data:
            print("No data to export.")
            return

        print(f"Exporting data to {filename}...")

        # Define CSV columns
        fieldnames = [
            "Organization",
            "Repository",
            "Description",
            "URL",
            "Is_Private",
            "Is_Fork",
            "Is_Archived",
            "Created_At",
            "Updated_At",
            "Pushed_At",
            "Size_KB",
            "Default_Branch",
            "Forks",
            "Open_Issues",
            "Pull_Requests",
            "Releases",
            "Branches",
            "Tags",
            "Workflows",
            "Repo_Webhooks",
            "Org_Webhooks",
            "GitHub_Apps",
        ]

        with open(filename, "w", newline="", encoding="utf-8") as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(self.inventory_data)

        print(
            f"[OK] Successfully exported {len(self.inventory_data)} records to {filename}"
        )

        # Print summary statistics
        self.print_summary()

    def print_summary(self):
        """Print summary statistics"""
        if not self.inventory_data:
            return

        total_repos = len(self.inventory_data)
        total_workflows = sum(r["Workflows"] for r in self.inventory_data)
        total_webhooks = sum(r["Repo_Webhooks"] for r in self.inventory_data)
        total_branches = sum(r["Branches"] for r in self.inventory_data)
        total_apps = sum(r["GitHub_Apps"] for r in self.inventory_data)
        total_prs = sum(r["Pull_Requests"] for r in self.inventory_data)
        total_issues = sum(r["Open_Issues"] for r in self.inventory_data)
        private_repos = sum(1 for r in self.inventory_data if r["Is_Private"])
        internal_repos = sum(1 for r in self.inventory_data if r["Is_Internal"])
        public_repos = sum(1 for r in self.inventory_data if r["Is_Public"])
        archived_repos = sum(1 for r in self.inventory_data if r["Is_Archived"])

        # Log summary statistics
        logging.info("=" * 60)
        logging.info("INVENTORY SUMMARY")
        logging.info(f"Total Repositories: {total_repos}")
        logging.info(f"Private Repositories: {private_repos}")
        logging.info(f"Internal Repositories: {internal_repos}")
        logging.info(f"Public Repositories: {public_repos}")
        logging.info(f"Archived Repositories: {archived_repos}")
        logging.info(f"Total Branches: {total_branches}")
        logging.info(f"Total Workflows: {total_workflows}")
        logging.info(f"Total Webhooks: {total_webhooks}")
        logging.info(f"Total GitHub Apps: {total_apps}")
        logging.info(f"Total Pull Requests: {total_prs}")
        logging.info(f"Total Open Issues: {total_issues}")
        logging.info("=" * 60)

        print("\n" + "=" * 60)
        print("INVENTORY SUMMARY")
        print("=" * 60)
        print(f"Total Repositories:        {total_repos:,}")
        print(f"Private Repositories:      {private_repos:,}")
        print(f"Internal Repositories:     {internal_repos:,}")
        print(f"Public Repositories:       {public_repos:,}")
        print(f"Archived Repositories:     {archived_repos:,}")
        print(f"Total Branches:            {total_branches:,}")
        print(f"Total Workflows:           {total_workflows:,}")
        print(f"Total Webhooks:            {total_webhooks:,}")
        print(f"Total GitHub Apps:         {total_apps:,}")
        print(f"Total Pull Requests:       {total_prs:,}")
        print(f"Total Open Issues:         {total_issues:,}")
        print("=" * 60 + "\n")


def main():
    """Main execution function"""
    load_dotenv()

    # Create output directories
    os.makedirs("output", exist_ok=True)
    os.makedirs(os.path.join("output", "logs"), exist_ok=True)

    # Set up logging
    log_filename = os.path.join(
        "output", "logs", f"inventory_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
    )
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(message)s",
        handlers=[logging.FileHandler(log_filename), logging.StreamHandler()],
    )

    logging.info("Starting GitHub Enterprise Inventory Collection")
    logging.info(f"Log file: {log_filename}")

    # Load configuration from environment
    enterprise_name = os.getenv("GITHUB_ENTERPRISE_NAME")
    pats_string = os.getenv("GITHUB_PATS")
    graphql_url = os.getenv("GITHUB_GRAPHQL_URL", "https://api.github.com/graphql")
    api_url = os.getenv("GITHUB_API_URL", "https://api.github.com")
    repo_csv_file = os.getenv("REPO_CSV_FILE", "github_inventory_repositories.csv")
    org_csv_file = os.getenv("ORG_CSV_FILE", "github_inventory_organizations.csv")

    # Validate configuration
    if not enterprise_name:
        logging.error("GITHUB_ENTERPRISE_NAME not set in .env file")
        print("Error: GITHUB_ENTERPRISE_NAME not set in .env file")
        sys.exit(1)

    if not pats_string:
        logging.error("GITHUB_PATS not set in .env file")
        print("Error: GITHUB_PATS not set in .env file")
        sys.exit(1)

    logging.info(f"Configuration loaded - Enterprise: {enterprise_name}")

    # Parse PATs
    pats = [pat.strip() for pat in pats_string.split(",") if pat.strip()]
    logging.info(f"Parsed {len(pats)} Personal Access Token(s)")

    try:
        # Initialize PAT manager
        pat_manager = PATManager(pats)

        # Initialize inventory collector
        logging.info("Initializing inventory collector...")
        collector = GitHubInventoryCollector(
            enterprise_name=enterprise_name,
            pat_manager=pat_manager,
            graphql_url=graphql_url,
            api_url=api_url,
            repo_csv_file=repo_csv_file,
            org_csv_file=org_csv_file,
        )
        logging.info(
            f"Repository CSV will be saved to: {os.path.join('output', repo_csv_file)}"
        )
        logging.info(
            f"Organization CSV will be saved to: {os.path.join('output', org_csv_file)}"
        )

        # Collect inventory (data is written incrementally to CSV)
        collector.collect_inventory()

        # Print summary statistics
        collector.print_summary()

        logging.info("Inventory collection completed successfully!")
        print(f"\n[OK] Inventory collection completed successfully!")
        print(f"[OK] Repository data saved to: {os.path.join('output', repo_csv_file)}")
        print(
            f"[OK] Organization data saved to: {os.path.join('output', org_csv_file)}"
        )
        print(f"[OK] Log file saved to: {log_filename}")

    except KeyboardInterrupt:
        logging.warning("Operation cancelled by user")
        print("\n\nOperation cancelled by user.")
        sys.exit(0)
    except Exception as e:
        logging.error(f"Error: {e}")
        print(f"\n[ERROR] Error: {e}")
        import traceback

        logging.error(traceback.format_exc())
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
