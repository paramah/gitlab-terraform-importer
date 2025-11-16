"""Tests for ModuleDownloader."""

import tempfile
from pathlib import Path
from unittest.mock import MagicMock, Mock, patch
import pytest

from gitlab_terraform_importer.infrastructure.terraform.module_downloader import (
    ModuleDownloader,
)


class TestModuleDownloader:
    """Test ModuleDownloader class."""

    def test_download_module_local_path(self, tmp_path):
        """Test that local paths are returned as-is."""
        downloader = ModuleDownloader()

        # Create a test module directory
        module_dir = tmp_path / "test_module"
        module_dir.mkdir()
        (module_dir / "main.tf").write_text("# test")

        result = downloader.download_module(str(module_dir))

        assert result == module_dir
        assert result.exists()

    def test_download_module_local_path_with_subdirectory(self, tmp_path):
        """Test local path with subdirectory."""
        downloader = ModuleDownloader()

        # Create a test module directory with subdirectory
        module_dir = tmp_path / "test_module"
        subdir = module_dir / "modules" / "gitlab"
        subdir.mkdir(parents=True)
        (subdir / "main.tf").write_text("# test")

        result = downloader.download_module(str(module_dir), subdirectory="modules/gitlab")

        assert result == subdir
        assert result.exists()

    def test_is_git_url_git_extension(self):
        """Test Git URL detection with .git extension."""
        downloader = ModuleDownloader()

        assert downloader._is_git_url("https://github.com/user/repo.git")
        assert downloader._is_git_url("git@github.com:user/repo.git")

    def test_is_git_url_github_url(self):
        """Test Git URL detection for GitHub without .git."""
        downloader = ModuleDownloader()

        assert downloader._is_git_url("https://github.com/user/repo")
        assert not downloader._is_git_url("https://github.com/user/repo.zip")

    def test_is_git_url_gitlab_url(self):
        """Test Git URL detection for GitLab."""
        downloader = ModuleDownloader()

        assert downloader._is_git_url("https://gitlab.com/user/repo")
        assert not downloader._is_git_url("https://gitlab.com/user/repo.tar.gz")

    def test_is_git_url_git_protocol(self):
        """Test Git URL detection with git:// protocol."""
        downloader = ModuleDownloader()

        assert downloader._is_git_url("git://example.com/repo")
        assert downloader._is_git_url("git@example.com:repo")

    def test_is_git_url_http_archive(self):
        """Test that HTTP archives are not detected as Git URLs."""
        downloader = ModuleDownloader()

        assert not downloader._is_git_url("https://example.com/module.zip")
        assert not downloader._is_git_url("https://example.com/module.tar.gz")

    @patch("subprocess.run")
    def test_clone_git_repository_success(self, mock_run):
        """Test successful Git repository clone."""
        downloader = ModuleDownloader()
        mock_run.return_value = Mock(returncode=0, stdout="", stderr="")

        result = downloader._clone_git_repository("https://github.com/user/repo.git")

        assert result.exists()
        assert result.is_dir()
        assert str(result).startswith(tempfile.gettempdir())

        # Verify git clone was called correctly
        mock_run.assert_called_once()
        call_args = mock_run.call_args[0][0]
        assert call_args[0] == "git"
        assert call_args[1] == "clone"
        assert call_args[2] == "--depth"
        assert call_args[3] == "1"
        assert call_args[4] == "https://github.com/user/repo.git"

        # Cleanup
        downloader.cleanup()

    @patch("subprocess.run")
    def test_clone_git_repository_failure(self, mock_run):
        """Test Git repository clone failure."""
        downloader = ModuleDownloader()
        mock_run.side_effect = Exception("Git clone failed")

        with pytest.raises(RuntimeError, match="Failed to clone Git repository"):
            downloader._clone_git_repository("https://github.com/user/repo.git")

    @patch("subprocess.run")
    def test_clone_git_repository_git_not_installed(self, mock_run):
        """Test Git repository clone when git is not installed."""
        downloader = ModuleDownloader()
        mock_run.side_effect = FileNotFoundError()

        with pytest.raises(RuntimeError, match="Git is not installed"):
            downloader._clone_git_repository("https://github.com/user/repo.git")

    @patch("urllib.request.urlretrieve")
    def test_download_http_archive_zip(self, mock_urlretrieve, tmp_path):
        """Test HTTP archive download (ZIP)."""
        downloader = ModuleDownloader()

        # Create a mock ZIP file
        import zipfile

        zip_path = tmp_path / "test.zip"
        with zipfile.ZipFile(zip_path, "w") as zf:
            zf.writestr("main.tf", "# test module")
            zf.writestr("variables.tf", "# variables")

        # Mock the download to use our test ZIP
        def mock_download(url, path):
            import shutil

            shutil.copy(zip_path, path)

        mock_urlretrieve.side_effect = mock_download

        result = downloader._download_http_archive("https://example.com/module.zip")

        assert result.exists()
        assert result.is_dir()
        assert (result / "main.tf").exists()
        assert (result / "variables.tf").exists()

        # Cleanup
        downloader.cleanup()

    @patch("urllib.request.urlretrieve")
    def test_download_http_archive_tar_gz(self, mock_urlretrieve, tmp_path):
        """Test HTTP archive download (TAR.GZ)."""
        downloader = ModuleDownloader()

        # Create a mock TAR.GZ file
        import tarfile

        tar_path = tmp_path / "test.tar.gz"
        with tarfile.open(tar_path, "w:gz") as tf:
            # Create temporary files to add to archive
            main_tf = tmp_path / "main.tf"
            main_tf.write_text("# test module")
            tf.add(main_tf, arcname="main.tf")

            vars_tf = tmp_path / "variables.tf"
            vars_tf.write_text("# variables")
            tf.add(vars_tf, arcname="variables.tf")

        # Mock the download to use our test TAR.GZ
        def mock_download(url, path):
            import shutil

            shutil.copy(tar_path, path)

        mock_urlretrieve.side_effect = mock_download

        result = downloader._download_http_archive("https://example.com/module.tar.gz")

        assert result.exists()
        assert result.is_dir()
        assert (result / "main.tf").exists()
        assert (result / "variables.tf").exists()

        # Cleanup
        downloader.cleanup()

    @patch("urllib.request.urlretrieve")
    def test_download_http_archive_with_top_level_directory(self, mock_urlretrieve, tmp_path):
        """Test HTTP archive that contains a top-level directory."""
        downloader = ModuleDownloader()

        # Create a mock ZIP file with a top-level directory
        import zipfile

        zip_path = tmp_path / "test.zip"
        with zipfile.ZipFile(zip_path, "w") as zf:
            zf.writestr("repo-main/main.tf", "# test module")
            zf.writestr("repo-main/variables.tf", "# variables")

        # Mock the download
        def mock_download(url, path):
            import shutil

            shutil.copy(zip_path, path)

        mock_urlretrieve.side_effect = mock_download

        result = downloader._download_http_archive("https://example.com/module.zip")

        # Should return the subdirectory containing .tf files
        assert result.exists()
        assert result.is_dir()
        assert (result / "main.tf").exists()
        assert (result / "variables.tf").exists()

        # Cleanup
        downloader.cleanup()

    @patch("urllib.request.urlretrieve")
    def test_download_http_archive_failure(self, mock_urlretrieve):
        """Test HTTP archive download failure."""
        downloader = ModuleDownloader()
        mock_urlretrieve.side_effect = Exception("Download failed")

        with pytest.raises(RuntimeError, match="Failed to download module"):
            downloader._download_http_archive("https://example.com/module.zip")

    def test_download_module_invalid_source(self):
        """Test download with invalid source."""
        downloader = ModuleDownloader()

        with pytest.raises(ValueError, match="Unsupported source format"):
            downloader.download_module("ftp://example.com/module")

    def test_find_module_root_direct_tf_files(self, tmp_path):
        """Test finding module root when .tf files are directly in the directory."""
        downloader = ModuleDownloader()

        extract_dir = tmp_path / "extracted"
        extract_dir.mkdir()
        (extract_dir / "main.tf").write_text("# test")

        result = downloader._find_module_root(extract_dir)

        assert result == extract_dir

    def test_find_module_root_single_subdirectory(self, tmp_path):
        """Test finding module root when there's a single subdirectory."""
        downloader = ModuleDownloader()

        extract_dir = tmp_path / "extracted"
        extract_dir.mkdir()
        subdir = extract_dir / "module"
        subdir.mkdir()
        (subdir / "main.tf").write_text("# test")

        result = downloader._find_module_root(extract_dir)

        assert result == subdir

    def test_find_module_root_no_tf_files(self, tmp_path):
        """Test finding module root when no .tf files are found."""
        downloader = ModuleDownloader()

        extract_dir = tmp_path / "extracted"
        extract_dir.mkdir()

        # Should return extract_dir even if no .tf files
        result = downloader._find_module_root(extract_dir)

        assert result == extract_dir

    def test_cleanup(self):
        """Test cleanup of temporary directories."""
        downloader = ModuleDownloader()

        # Create a temporary directory manually
        temp_dir = Path(tempfile.mkdtemp(prefix="terraform_module_test_"))
        downloader._temp_dirs.append(temp_dir)

        assert temp_dir.exists()

        downloader.cleanup()

        assert not temp_dir.exists()
        assert len(downloader._temp_dirs) == 0

    @patch("subprocess.run")
    def test_download_module_git_with_subdirectory(self, mock_run):
        """Test Git clone with subdirectory."""
        downloader = ModuleDownloader()
        mock_run.return_value = Mock(returncode=0, stdout="", stderr="")

        # Create the expected directory structure
        with patch.object(downloader, "_clone_git_repository") as mock_clone:
            temp_dir = Path(tempfile.mkdtemp())
            subdir = temp_dir / "modules" / "gitlab"
            subdir.mkdir(parents=True)
            (subdir / "main.tf").write_text("# test")

            mock_clone.return_value = temp_dir

            result = downloader.download_module(
                "https://github.com/user/repo.git", subdirectory="modules/gitlab"
            )

            assert result == subdir
            assert result.exists()

            # Cleanup
            import shutil

            shutil.rmtree(temp_dir)

    @patch("subprocess.run")
    def test_download_module_git_subdirectory_not_found(self, mock_run):
        """Test Git clone with non-existent subdirectory."""
        downloader = ModuleDownloader()
        mock_run.return_value = Mock(returncode=0, stdout="", stderr="")

        with patch.object(downloader, "_clone_git_repository") as mock_clone:
            temp_dir = Path(tempfile.mkdtemp())
            mock_clone.return_value = temp_dir

            with pytest.raises(ValueError, match="Subdirectory .* not found"):
                downloader.download_module(
                    "https://github.com/user/repo.git", subdirectory="nonexistent"
                )

            # Cleanup
            import shutil

            shutil.rmtree(temp_dir)
