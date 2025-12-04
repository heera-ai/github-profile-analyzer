import httpx
import re
import asyncio
from typing import Optional
from datetime import datetime, timezone, timedelta
from functools import lru_cache
import hashlib
import json


class SimpleCache:
    """Simple in-memory cache with TTL support."""

    def __init__(self, default_ttl: int = 3600):
        self._cache: dict[str, tuple[any, datetime]] = {}
        self.default_ttl = default_ttl  # 1 hour default

    def _make_key(self, *args) -> str:
        """Create cache key from arguments."""
        return hashlib.md5(json.dumps(args, sort_keys=True).encode()).hexdigest()

    def get(self, key: str) -> Optional[any]:
        """Get value from cache if not expired."""
        if key in self._cache:
            value, expires_at = self._cache[key]
            if datetime.now(timezone.utc) < expires_at:
                return value
            else:
                del self._cache[key]
        return None

    def set(self, key: str, value: any, ttl: Optional[int] = None):
        """Set value in cache with TTL."""
        ttl = ttl or self.default_ttl
        expires_at = datetime.now(timezone.utc) + timedelta(seconds=ttl)
        self._cache[key] = (value, expires_at)

    def clear(self):
        """Clear entire cache."""
        self._cache.clear()

    def stats(self) -> dict:
        """Get cache statistics."""
        now = datetime.now(timezone.utc)
        valid = sum(1 for _, (_, exp) in self._cache.items() if now < exp)
        return {"total_entries": len(self._cache), "valid_entries": valid}


# Global cache instance
cache = SimpleCache(default_ttl=3600)  # Cache for 1 hour


class GitHubService:
    BASE_URL = "https://api.github.com"

    def __init__(self, token: Optional[str] = None):
        self.headers = {
            "Accept": "application/vnd.github.v3+json",
            "User-Agent": "GitHub-Profile-Analyzer"
        }
        self.token = token
        if token:
            self.headers["Authorization"] = f"Bearer {token}"

        self._rate_limit_remaining = None
        self._rate_limit_reset = None

    def _extract_username(self, query: str) -> str:
        """Extract username from URL, email, or direct username."""
        query = query.strip()

        # GitHub URL pattern
        url_pattern = r"(?:https?://)?(?:www\.)?github\.com/([a-zA-Z0-9-]+)"
        match = re.match(url_pattern, query)
        if match:
            return match.group(1)

        # Email pattern - we'll search for it
        if "@" in query:
            return query  # Return as-is, will search by email

        # Assume it's a username
        return query

    def _update_rate_limit(self, response: httpx.Response):
        """Update rate limit info from response headers."""
        self._rate_limit_remaining = int(response.headers.get("x-ratelimit-remaining", 0))
        reset_timestamp = int(response.headers.get("x-ratelimit-reset", 0))
        self._rate_limit_reset = datetime.fromtimestamp(reset_timestamp, tz=timezone.utc) if reset_timestamp else None

    def get_rate_limit_info(self) -> dict:
        """Get current rate limit information."""
        return {
            "remaining": self._rate_limit_remaining,
            "reset_at": self._rate_limit_reset.isoformat() if self._rate_limit_reset else None,
            "has_token": bool(self.token)
        }

    async def _request(self, client: httpx.AsyncClient, method: str, url: str, **kwargs) -> httpx.Response:
        """Make HTTP request with rate limit handling."""
        response = await client.request(method, url, headers=self.headers, **kwargs)
        self._update_rate_limit(response)

        if response.status_code == 403 and "rate limit" in response.text.lower():
            reset_time = self._rate_limit_reset
            if reset_time:
                wait_seconds = (reset_time - datetime.now(timezone.utc)).total_seconds()
                raise Exception(f"Rate limit exceeded. Resets in {int(wait_seconds)} seconds. Add GITHUB_TOKEN to .env file for 5000 requests/hour.")
            raise Exception("Rate limit exceeded. Add GITHUB_TOKEN to .env file for 5000 requests/hour.")

        return response

    async def search_user_by_email(self, email: str) -> Optional[str]:
        """Search for a user by email."""
        cache_key = cache._make_key("search_email", email)
        cached = cache.get(cache_key)
        if cached is not None:
            return cached

        async with httpx.AsyncClient() as client:
            response = await self._request(
                client, "GET",
                f"{self.BASE_URL}/search/users",
                params={"q": f"{email} in:email"}
            )
            if response.status_code == 200:
                data = response.json()
                if data.get("total_count", 0) > 0:
                    result = data["items"][0]["login"]
                    cache.set(cache_key, result)
                    return result

        cache.set(cache_key, "")  # Cache negative result
        return None

    async def get_user(self, username: str) -> dict:
        """Get user profile data."""
        cache_key = cache._make_key("user", username.lower())
        cached = cache.get(cache_key)
        if cached:
            return cached

        async with httpx.AsyncClient() as client:
            response = await self._request(
                client, "GET",
                f"{self.BASE_URL}/users/{username}"
            )
            response.raise_for_status()
            data = response.json()
            cache.set(cache_key, data)
            return data

    async def get_repos(self, username: str, per_page: int = 100) -> list[dict]:
        """Get all public repositories for a user."""
        cache_key = cache._make_key("repos", username.lower())
        cached = cache.get(cache_key)
        if cached:
            return cached

        repos = []
        page = 1

        async with httpx.AsyncClient() as client:
            while True:
                response = await self._request(
                    client, "GET",
                    f"{self.BASE_URL}/users/{username}/repos",
                    params={
                        "per_page": per_page,
                        "page": page,
                        "sort": "updated",
                        "type": "owner"
                    }
                )
                response.raise_for_status()
                data = response.json()

                if not data:
                    break

                repos.extend(data)
                page += 1

                # Limit to avoid rate limits
                if page > 5:
                    break

        cache.set(cache_key, repos)
        return repos

    async def get_repo_languages(self, username: str, repo_name: str) -> dict:
        """Get languages used in a repository."""
        cache_key = cache._make_key("languages", username.lower(), repo_name.lower())
        cached = cache.get(cache_key)
        if cached is not None:
            return cached

        async with httpx.AsyncClient() as client:
            response = await self._request(
                client, "GET",
                f"{self.BASE_URL}/repos/{username}/{repo_name}/languages"
            )
            if response.status_code == 200:
                data = response.json()
                cache.set(cache_key, data)
                return data

            cache.set(cache_key, {})
            return {}

    async def get_multiple_repo_languages(self, username: str, repo_names: list[str]) -> dict[str, dict]:
        """Fetch languages for multiple repos concurrently."""
        async def fetch_one(repo_name: str) -> tuple[str, dict]:
            langs = await self.get_repo_languages(username, repo_name)
            return repo_name, langs

        tasks = [fetch_one(name) for name in repo_names]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        return {
            name: langs for name, langs in results
            if not isinstance(langs, Exception) and isinstance(name, str)
        }

    async def get_events(self, username: str, per_page: int = 100) -> list[dict]:
        """Get recent public events for activity analysis."""
        cache_key = cache._make_key("events", username.lower())
        cached = cache.get(cache_key)
        if cached:
            return cached

        events = []
        page = 1

        async with httpx.AsyncClient() as client:
            while page <= 3:  # GitHub limits to 300 events
                response = await self._request(
                    client, "GET",
                    f"{self.BASE_URL}/users/{username}/events/public",
                    params={"per_page": per_page, "page": page}
                )
                if response.status_code != 200:
                    break

                data = response.json()
                if not data:
                    break

                events.extend(data)
                page += 1

        cache.set(cache_key, events, ttl=1800)  # Cache events for 30 min
        return events

    async def get_orgs(self, username: str) -> list[str]:
        """Get organizations the user belongs to."""
        cache_key = cache._make_key("orgs", username.lower())
        cached = cache.get(cache_key)
        if cached is not None:
            return cached

        async with httpx.AsyncClient() as client:
            response = await self._request(
                client, "GET",
                f"{self.BASE_URL}/users/{username}/orgs"
            )
            if response.status_code == 200:
                result = [org["login"] for org in response.json()]
                cache.set(cache_key, result)
                return result

            cache.set(cache_key, [])
            return []

    async def get_contribution_stats(self, username: str) -> dict:
        """Get contribution statistics from events."""
        events = await self.get_events(username)

        push_events = [e for e in events if e["type"] == "PushEvent"]
        pr_events = [e for e in events if e["type"] == "PullRequestEvent"]
        issue_events = [e for e in events if e["type"] == "IssuesEvent"]

        # Analyze commit times
        commit_hours = []
        commit_days = []

        for event in push_events:
            created_at = datetime.fromisoformat(event["created_at"].replace("Z", "+00:00"))
            commit_hours.append(created_at.hour)
            commit_days.append(created_at.strftime("%A"))

        return {
            "total_push_events": len(push_events),
            "total_pr_events": len(pr_events),
            "total_issue_events": len(issue_events),
            "commit_hours": commit_hours,
            "commit_days": commit_days,
            "events": events
        }

    async def resolve_username(self, query: str) -> str:
        """Resolve query to username."""
        extracted = self._extract_username(query)

        # If it looks like an email, search for it
        if "@" in extracted:
            found = await self.search_user_by_email(extracted)
            if found:
                return found
            raise ValueError(f"No GitHub user found with email: {extracted}")

        return extracted


def get_cache_stats() -> dict:
    """Get cache statistics."""
    return cache.stats()


def clear_cache():
    """Clear the cache."""
    cache.clear()
