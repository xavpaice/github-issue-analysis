"""GitHub attachment detection and download functionality."""

import asyncio
import re
from pathlib import Path
from urllib.parse import urlparse

import httpx
from rich.console import Console

from .models import GitHubAttachment, GitHubIssue

console = Console()

# Regex patterns for GitHub attachment URLs
GITHUB_FILE_PATTERN = r"https://github\.com/[\w-]+/[\w-]+/files/\d+/[\w.-]+\??[\w=&]*"
GITHUB_IMAGE_PATTERN = (
    r"https://user-images\.githubusercontent\.com/\d+/[\w.-]+\??[\w=&]*"
)
GITHUB_ASSET_PATTERN = r"https://github\.com/[\w-]+/[\w-]+/assets/\d+"


class AttachmentDownloader:
    """Downloads and manages GitHub issue attachments."""

    def __init__(self, github_token: str, max_size_mb: int = 10):
        """Initialize attachment downloader.

        Args:
            github_token: GitHub personal access token
            max_size_mb: Maximum file size to download in MB
        """
        self.github_token = github_token
        self.max_size_bytes = max_size_mb * 1024 * 1024
        self.headers = {
            "Authorization": f"token {github_token}",
            "User-Agent": "github-issue-analysis/0.1.0",
        }

    def detect_attachments(self, text: str, source: str) -> list[GitHubAttachment]:
        """Detect GitHub attachments in text content.

        Args:
            text: Text content to search for attachments
            source: Source identifier (e.g., "issue_body", "comment_123")

        Returns:
            List of detected GitHubAttachment objects
        """
        if not text:
            return []

        attachments = []

        # Find all GitHub file URLs
        file_urls = re.findall(GITHUB_FILE_PATTERN, text)
        for url in file_urls:
            filename = self._extract_filename(url)
            attachments.append(
                GitHubAttachment(original_url=url, filename=filename, source=source)
            )

        # Find all GitHub image URLs
        image_urls = re.findall(GITHUB_IMAGE_PATTERN, text)
        for url in image_urls:
            filename = self._extract_filename(url)
            attachments.append(
                GitHubAttachment(original_url=url, filename=filename, source=source)
            )

        # Find all GitHub asset URLs
        asset_urls = re.findall(GITHUB_ASSET_PATTERN, text)
        for url in asset_urls:
            filename = self._extract_filename(url)
            attachments.append(
                GitHubAttachment(original_url=url, filename=filename, source=source)
            )

        return attachments

    def _extract_filename(self, url: str) -> str:
        """Extract filename from URL.

        Args:
            url: URL to extract filename from

        Returns:
            Extracted filename or generated name
        """
        parsed = urlparse(url)
        path_parts = parsed.path.split("/")

        # For GitHub files, filename is usually the last part
        if path_parts:
            filename = path_parts[-1]
            # Remove query parameters
            if "?" in filename:
                filename = filename.split("?")[0]
            if filename and filename != "/":
                return filename

        # Generate filename from URL if extraction fails
        return f"attachment_{hash(url) % 10000}"

    def _generate_safe_filename(self, filename: str, download_dir: Path) -> str:
        """Generate a safe filename, handling duplicates.

        Args:
            filename: Original filename
            download_dir: Directory where file will be saved

        Returns:
            Safe filename that doesn't conflict with existing files
        """
        # Remove or replace unsafe characters
        safe_chars = set(
            "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789.-_"
        )
        safe_filename = "".join(c if c in safe_chars else "_" for c in filename)

        # Ensure filename is not empty
        if not safe_filename:
            safe_filename = "attachment"

        # Handle duplicate filenames
        counter = 1
        original_name = safe_filename
        while (download_dir / safe_filename).exists():
            name_parts = original_name.rsplit(".", 1)
            if len(name_parts) == 2:
                safe_filename = f"{name_parts[0]}_{counter}.{name_parts[1]}"
            else:
                safe_filename = f"{original_name}_{counter}"
            counter += 1

        return safe_filename

    async def download_attachment(
        self, attachment: GitHubAttachment, download_dir: Path
    ) -> GitHubAttachment:
        """Download a single attachment.

        Args:
            attachment: GitHubAttachment object to download
            download_dir: Directory to save the attachment

        Returns:
            Updated GitHubAttachment object with download status
        """
        try:
            async with httpx.AsyncClient() as client:
                # First, get file info with HEAD request
                head_response = await client.head(
                    attachment.original_url, headers=self.headers, follow_redirects=True
                )

                # Check file size
                content_length = head_response.headers.get("content-length")
                if content_length:
                    size = int(content_length)
                    if size > self.max_size_bytes:
                        console.print(
                            f"⚠️  Skipping {attachment.filename}: "
                            f"File too large ({size / 1024 / 1024:.1f} MB > "
                            f"{self.max_size_bytes / 1024 / 1024} MB)"
                        )
                        return attachment
                    attachment.size = size

                # Get content type
                content_type = head_response.headers.get("content-type")
                if content_type:
                    attachment.content_type = content_type

                # Download the file
                response = await client.get(
                    attachment.original_url, headers=self.headers, follow_redirects=True
                )
                response.raise_for_status()

                # Generate safe filename
                safe_filename = self._generate_safe_filename(
                    attachment.filename, download_dir
                )
                file_path = download_dir / safe_filename

                # Save file
                with open(file_path, "wb") as f:
                    f.write(response.content)

                # Update attachment info
                attachment.local_path = str(file_path)
                attachment.downloaded = True
                attachment.size = len(response.content)

                console.print(f"✅ Downloaded: {safe_filename}")
                return attachment

        except httpx.HTTPStatusError as e:
            console.print(
                f"❌ HTTP error downloading {attachment.filename}: "
                f"{e.response.status_code} {e.response.reason_phrase}"
            )
        except Exception as e:
            console.print(f"❌ Error downloading {attachment.filename}: {e}")

        return attachment

    async def download_attachments(
        self, attachments: list[GitHubAttachment], download_dir: Path
    ) -> list[GitHubAttachment]:
        """Download multiple attachments concurrently.

        Args:
            attachments: List of GitHubAttachment objects to download
            download_dir: Directory to save attachments

        Returns:
            List of updated GitHubAttachment objects
        """
        if not attachments:
            return []

        # Create download directory
        download_dir.mkdir(parents=True, exist_ok=True)

        # Download attachments concurrently
        tasks = [
            self.download_attachment(attachment, download_dir)
            for attachment in attachments
        ]

        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Filter out exceptions and return successful downloads
        updated_attachments = []
        for result in results:
            if isinstance(result, GitHubAttachment):
                updated_attachments.append(result)
            else:
                console.print(f"❌ Download task failed: {result}")

        return updated_attachments

    def process_issue_attachments(self, issue: GitHubIssue) -> GitHubIssue:
        """Process and detect all attachments in an issue.

        Args:
            issue: GitHubIssue object to process

        Returns:
            Updated GitHubIssue object with detected attachments
        """
        all_attachments = []

        # Process issue body
        if issue.body:
            body_attachments = self.detect_attachments(issue.body, "issue_body")
            all_attachments.extend(body_attachments)

        # Process comments
        for comment in issue.comments:
            if comment.body:
                comment_attachments = self.detect_attachments(
                    comment.body, f"comment_{comment.id}"
                )
                all_attachments.extend(comment_attachments)

        # Update issue with attachments
        issue.attachments = all_attachments
        return issue

    async def download_issue_attachments(
        self, issue: GitHubIssue, base_dir: Path, org: str, repo: str
    ) -> GitHubIssue:
        """Download all attachments for an issue.

        Args:
            issue: GitHubIssue object with detected attachments
            base_dir: Base directory for attachments
            org: Organization name
            repo: Repository name

        Returns:
            Updated GitHubIssue object with downloaded attachments
        """
        if not issue.attachments:
            return issue

        # Create issue-specific directory
        issue_dir = base_dir / f"{org}_{repo}_issue_{issue.number}"

        console.print(
            f"📥 Downloading {len(issue.attachments)} attachments for "
            f"issue #{issue.number}"
        )

        # Download attachments
        updated_attachments = await self.download_attachments(
            issue.attachments, issue_dir
        )

        # Update issue with downloaded attachments
        issue.attachments = updated_attachments

        # Count successful downloads
        downloaded_count = sum(1 for att in updated_attachments if att.downloaded)
        console.print(
            f"✅ Downloaded {downloaded_count}/{len(updated_attachments)} attachments"
        )

        return issue
