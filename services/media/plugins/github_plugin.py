import requests
import re
import time
from services.media.plugins.base import MediaPlugin

class GitHubPlugin(MediaPlugin):
    @property
    def name(self) -> str:
        return "github"

    def extract(self, source: str, source_id: int = None) -> tuple[str, str, str, int]:
        """
        Extract repository metadata and README.
        Returns: (raw_text, title, channel/owner, duration)
        """
        t0 = time.time()
        
        # Parse owner and repo from URL
        match = re.search(r'github\.com/([^/]+)/([^/]+)', source)
        if not match:
            raise ValueError("Invalid GitHub URL format")
            
        owner = match.group(1)
        repo = match.group(2).split('.git')[0]
        
        api_base = f"https://api.github.com/repos/{owner}/{repo}"
        headers = {"Accept": "application/vnd.github.v3+json"}
        
        try:
            # 1. Fetch Repo Metadata
            repo_resp = requests.get(api_base, headers=headers, timeout=10)
            repo_resp.raise_for_status()
            repo_data = repo_resp.json()
            
            description = repo_data.get("description", "No description provided.")
            topics = repo_data.get("topics", [])
            title = f"{owner}/{repo}"
            
            # 2. Fetch Languages
            lang_resp = requests.get(f"{api_base}/languages", headers=headers, timeout=5)
            languages = list(lang_resp.json().keys()) if lang_resp.status_code == 200 else []
            
            # 3. Fetch README
            readme_resp = requests.get(f"{api_base}/readme", headers={"Accept": "application/vnd.github.v3.raw"}, timeout=10)
            readme_text = readme_resp.text if readme_resp.status_code == 200 else "No README found."
            
            # Combine
            content = f"Repository: {title}\n"
            content += f"Description: {description}\n"
            if topics:
                content += f"Topics: {', '.join(topics)}\n"
            if languages:
                content += f"Languages: {', '.join(languages)}\n"
            content += "\n--- README ---\n\n"
            content += readme_text
            
            elapsed = time.time() - t0
            print(f"[PERF] GitHub Extraction: {elapsed:.2f}s")
            
            return {
                "transcript": content,
                "title": title,
                "channel": owner,
                "duration": 0,
                "video_id": f"github:{owner}/{repo}",
                "extraction_method": "github_api"
            }
            
        except Exception as e:
            elapsed = time.time() - t0
            print(f"[PERF] GitHub Extraction: {elapsed:.2f}s (Failed)")
            raise Exception(f"Failed to fetch from GitHub API: {e}")
