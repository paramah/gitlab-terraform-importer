"""Module downloader for HTTP and Git sources."""

import logging
import shutil
import subprocess
import tempfile
import urllib.request
import zipfile
import tarfile
from pathlib import Path
from typing import Optional, Tuple
from urllib.parse import urlparse
import atexit

logger = logging.getLogger(__name__)


class ModuleDownloader:
    """Downloads Terraform modules from HTTP or Git sources."""

    def __init__(self):
        """Initialize the module downloader."""
        self._temp_dirs: list[Path] = []
        # Register cleanup on exit
        atexit.register(self.cleanup)

    def download_module(self, source: str, subdirectory: Optional[str] = None) -> Path:
        """Download a module from a URL or clone from Git.

        Args:
            source: HTTP URL, Git URL, or local path
            subdirectory: Optional subdirectory within the downloaded module

        Returns:
            Path to the downloaded module directory

        Raises:
            ValueError: If source format is invalid
            RuntimeError: If download or clone fails
        """
        logger.info(f"Processing module source: {source}")

        # Check if it's a local path
        local_path = Path(source)
        if local_path.exists() and local_path.is_dir():
            logger.info(f"Using local module at: {source}")
            if subdirectory:
                return local_path / subdirectory
            return local_path

        # Parse the URL
        parsed_url = urlparse(source)

        # Determine source type
        if self._is_git_url(source):
            module_path = self._clone_git_repository(source)
        elif parsed_url.scheme in ['http', 'https']:
            module_path = self._download_http_archive(source)
        else:
            raise ValueError(
                f"Unsupported source format: {source}. "
                "Supported formats: HTTP(S) URL, Git URL, or local path"
            )

        # Handle subdirectory if specified
        if subdirectory:
            final_path = module_path / subdirectory
            if not final_path.exists():
                raise ValueError(
                    f"Subdirectory '{subdirectory}' not found in downloaded module"
                )
            return final_path

        return module_path

    def _is_git_url(self, url: str) -> bool:
        """Check if URL is a Git repository.

        Args:
            url: URL to check

        Returns:
            True if URL is a Git repository
        """
        # Common Git URL patterns
        git_patterns = [
            url.endswith('.git'),
            url.startswith('git@'),
            url.startswith('git://'),
            'github.com' in url and not url.endswith(('.zip', '.tar.gz', '.tar')),
            'gitlab.com' in url and not url.endswith(('.zip', '.tar.gz', '.tar')),
            'bitbucket.org' in url and not url.endswith(('.zip', '.tar.gz', '.tar')),
        ]
        return any(git_patterns)

    def _clone_git_repository(self, git_url: str) -> Path:
        """Clone a Git repository to a temporary directory.

        Args:
            git_url: Git repository URL

        Returns:
            Path to cloned repository

        Raises:
            RuntimeError: If git clone fails
        """
        logger.info(f"Cloning Git repository: {git_url}")

        # Create temporary directory
        temp_dir = Path(tempfile.mkdtemp(prefix='terraform_module_git_'))
        self._temp_dirs.append(temp_dir)

        try:
            # Clone the repository
            result = subprocess.run(
                ['git', 'clone', '--depth', '1', git_url, str(temp_dir)],
                capture_output=True,
                text=True,
                check=True
            )
            logger.info(f"Successfully cloned repository to: {temp_dir}")
            return temp_dir

        except subprocess.CalledProcessError as e:
            logger.error(f"Git clone failed: {e.stderr}")
            raise RuntimeError(f"Failed to clone Git repository: {e.stderr}")
        except FileNotFoundError:
            raise RuntimeError(
                "Git is not installed or not available in PATH. "
                "Please install Git to download modules from Git repositories."
            )

    def _download_http_archive(self, url: str) -> Path:
        """Download and extract an archive from HTTP(S).

        Args:
            url: HTTP(S) URL to archive

        Returns:
            Path to extracted archive

        Raises:
            RuntimeError: If download or extraction fails
        """
        logger.info(f"Downloading archive from: {url}")

        # Create temporary directory
        temp_dir = Path(tempfile.mkdtemp(prefix='terraform_module_http_'))
        self._temp_dirs.append(temp_dir)

        # Determine archive type from URL
        archive_path = temp_dir / "archive"
        if url.endswith('.zip'):
            archive_path = temp_dir / "archive.zip"
        elif url.endswith('.tar.gz') or url.endswith('.tgz'):
            archive_path = temp_dir / "archive.tar.gz"
        elif url.endswith('.tar'):
            archive_path = temp_dir / "archive.tar"
        else:
            # Try to guess from content-type or default to zip
            archive_path = temp_dir / "archive.zip"

        try:
            # Download the file
            logger.info(f"Downloading to: {archive_path}")
            urllib.request.urlretrieve(url, archive_path)

            # Extract the archive
            extract_dir = temp_dir / "extracted"
            extract_dir.mkdir(exist_ok=True)

            if archive_path.name.endswith('.zip'):
                self._extract_zip(archive_path, extract_dir)
            elif archive_path.name.endswith(('.tar.gz', '.tgz', '.tar')):
                self._extract_tar(archive_path, extract_dir)
            else:
                raise ValueError(f"Unsupported archive format: {archive_path.name}")

            # Find the module directory
            module_path = self._find_module_root(extract_dir)
            logger.info(f"Successfully extracted archive to: {module_path}")
            return module_path

        except Exception as e:
            logger.error(f"Failed to download or extract archive: {e}")
            raise RuntimeError(f"Failed to download module from {url}: {e}")

    def _extract_zip(self, archive_path: Path, extract_dir: Path) -> None:
        """Extract a ZIP archive.

        Args:
            archive_path: Path to ZIP file
            extract_dir: Directory to extract to
        """
        logger.info(f"Extracting ZIP archive: {archive_path}")
        with zipfile.ZipFile(archive_path, 'r') as zip_ref:
            zip_ref.extractall(extract_dir)

    def _extract_tar(self, archive_path: Path, extract_dir: Path) -> None:
        """Extract a TAR archive.

        Args:
            archive_path: Path to TAR file
            extract_dir: Directory to extract to
        """
        logger.info(f"Extracting TAR archive: {archive_path}")
        with tarfile.open(archive_path, 'r:*') as tar_ref:
            tar_ref.extractall(extract_dir)

    def _find_module_root(self, extract_dir: Path) -> Path:
        """Find the root directory containing Terraform files.

        Some archives contain a single top-level directory, others have files at root.

        Args:
            extract_dir: Directory where archive was extracted

        Returns:
            Path to module root directory
        """
        # Check if there are .tf files directly in extract_dir
        tf_files = list(extract_dir.glob('*.tf'))
        if tf_files:
            return extract_dir

        # Check if there's a single subdirectory
        subdirs = [d for d in extract_dir.iterdir() if d.is_dir()]
        if len(subdirs) == 1:
            # Check if this subdirectory contains .tf files
            single_subdir = subdirs[0]
            tf_files_in_subdir = list(single_subdir.glob('*.tf'))
            if tf_files_in_subdir:
                return single_subdir

        # If no .tf files found, return extract_dir anyway
        # (the parser will handle the error if it's not a valid module)
        logger.warning(
            f"No .tf files found in extracted archive. "
            f"Using extract directory: {extract_dir}"
        )
        return extract_dir

    def cleanup(self) -> None:
        """Clean up temporary directories."""
        for temp_dir in self._temp_dirs:
            if temp_dir.exists():
                try:
                    shutil.rmtree(temp_dir)
                    logger.debug(f"Cleaned up temporary directory: {temp_dir}")
                except Exception as e:
                    logger.warning(f"Failed to clean up {temp_dir}: {e}")
        self._temp_dirs.clear()

    def __del__(self):
        """Cleanup on deletion."""
        self.cleanup()
