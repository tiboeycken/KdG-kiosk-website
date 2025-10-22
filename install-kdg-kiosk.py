#!/usr/bin/env python3
"""
KdG Kiosk Installer
===================
Standalone installer for KdG Kiosk that downloads and installs the .deb package
from GitHub Releases with progress tracking.

Usage:
    python3 install-kdg-kiosk.py [--cli] [--version VERSION]

Options:
    --cli           Force CLI mode (no GUI)
    --version       Specify version to install (default: latest)
"""

import os
import sys
import subprocess
import urllib.request
import urllib.error
import json
import tempfile
import shutil
import platform
import argparse
from pathlib import Path

# Configuration
GITHUB_REPO = "Brasco123/KdG-Kiosk"  # UPDATE THIS!
PACKAGE_NAME = "kdg-kiosk"
DEB_PATTERN = "kdg-kiosk_{version}_amd64.deb"

# Try to import GUI libraries
try:
    from PyQt5.QtWidgets import (
        QApplication,
        QDialog,
        QVBoxLayout,
        QLabel,
        QProgressBar,
        QPushButton,
        QMessageBox,
        QTextEdit,
    )
    from PyQt5.QtCore import QThread, pyqtSignal, Qt
    from PyQt5.QtGui import QFont

    GUI_AVAILABLE = True
except ImportError:
    GUI_AVAILABLE = False


# ============================================================================
# Utility Functions
# ============================================================================


def check_root():
    """Check if running as root/sudo"""
    return os.geteuid() == 0


def check_system_compatibility():
    """Check if the system is compatible"""
    errors = []

    # Check OS
    if platform.system() != "Linux":
        errors.append("This installer only works on Linux systems.")

    # Check distribution
    try:
        with open("/etc/os-release") as f:
            os_release = f.read()
            if (
                "debian" not in os_release.lower()
                and "ubuntu" not in os_release.lower()
            ):
                errors.append("This package is designed for Debian/Ubuntu systems.")
    except FileNotFoundError:
        errors.append("Could not detect Linux distribution.")

    # Check architecture
    arch = platform.machine()
    if arch not in ["x86_64", "amd64"]:
        errors.append(
            f"Unsupported architecture: {arch}. Only amd64/x86_64 is supported."
        )

    # Check if apt/dpkg is available
    if not shutil.which("dpkg"):
        errors.append("dpkg not found. This installer requires dpkg.")

    if not shutil.which("apt"):
        errors.append("apt not found. This installer requires apt.")

    return errors


def get_latest_release_info(repo):
    """Fetch latest release information from GitHub"""
    url = f"https://api.github.com/repos/{repo}/releases/latest"

    try:
        with urllib.request.urlopen(url, timeout=10) as response:
            data = json.loads(response.read().decode())
            return {
                "version": data["tag_name"].lstrip("v"),
                "assets": data["assets"],
                "name": data["name"],
                "body": data.get("body", ""),
            }
    except urllib.error.HTTPError as e:
        if e.code == 404:
            raise Exception(
                "No releases found. Please create a release on GitHub first."
            )
        raise Exception(f"Failed to fetch release info: {e}")
    except Exception as e:
        raise Exception(f"Failed to connect to GitHub: {e}")


def find_deb_asset(assets, version):
    """Find the .deb file in release assets"""
    deb_name = DEB_PATTERN.format(version=version)

    for asset in assets:
        if asset["name"] == deb_name or asset["name"].endswith(".deb"):
            return asset["browser_download_url"], asset["name"]

    raise Exception(f"Could not find .deb file in release assets. Expected: {deb_name}")


def download_file(url, dest_path, progress_callback=None):
    """Download file with progress tracking"""

    def reporthook(block_num, block_size, total_size):
        if progress_callback and total_size > 0:
            downloaded = block_num * block_size
            percent = min(100, (downloaded * 100) // total_size)
            progress_callback(percent, downloaded, total_size)

    try:
        urllib.request.urlretrieve(url, dest_path, reporthook=reporthook)
        return True
    except Exception as e:
        raise Exception(f"Download failed: {e}")


def install_deb(deb_path, progress_callback=None):
    """Install .deb package with progress tracking"""

    if progress_callback:
        progress_callback("Installing dependencies...")

    # First, try to install with apt (handles dependencies better)
    try:
        # Install .deb with apt
        cmd = ["sudo", "apt", "install", "-y", deb_path]
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            universal_newlines=True,
        )

        output_lines = []
        for line in process.stdout:
            output_lines.append(line)
            if progress_callback:
                progress_callback(line.strip())

        process.wait()

        if process.returncode != 0:
            raise Exception(f"Installation failed:\n{''.join(output_lines)}")

        return True, "".join(output_lines)

    except Exception as e:
        # Fallback to dpkg
        if progress_callback:
            progress_callback("Trying alternative installation method...")

        try:
            # Install with dpkg
            subprocess.run(
                ["sudo", "dpkg", "-i", deb_path],
                check=True,
                capture_output=True,
                text=True,
            )

            # Fix dependencies
            subprocess.run(
                ["sudo", "apt", "install", "-f", "-y"],
                check=True,
                capture_output=True,
                text=True,
            )

            return True, "Installation completed successfully"
        except subprocess.CalledProcessError as e:
            raise Exception(f"Installation failed: {e.stderr}")


def check_dependencies():
    """Check if required dependencies are installed"""
    required = ["python3", "python3-pyqt5"]
    missing = []

    for dep in required:
        try:
            result = subprocess.run(["dpkg", "-s", dep], capture_output=True, text=True)
            if result.returncode != 0:
                missing.append(dep)
        except:
            missing.append(dep)

    return missing


# ============================================================================
# CLI Interface
# ============================================================================


class CLIInstaller:
    """Command-line installer with progress bars"""

    def __init__(self, version=None):
        self.version = version

    def print_header(self):
        """Print installer header"""
        print("\n" + "=" * 60)
        print("  KdG Kiosk Installer")
        print("=" * 60 + "\n")

    def print_progress_bar(self, percent, prefix="", suffix="", length=40):
        """Print a progress bar"""
        filled = int(length * percent // 100)
        bar = "█" * filled + "-" * (length - filled)
        print(f"\r{prefix} |{bar}| {percent}% {suffix}", end="", flush=True)

    def run(self):
        """Run CLI installation"""
        self.print_header()

        # Check system compatibility
        print("⚙️  Checking system compatibility...")
        errors = check_system_compatibility()
        if errors:
            print("\n❌ System compatibility check failed:")
            for error in errors:
                print(f"   • {error}")
            return False
        print("✓ System compatible\n")

        # Check if running with sudo
        if not check_root():
            print("⚠️  This installer requires sudo privileges.")
            print("   Please run: sudo python3 install-kdg-kiosk.py\n")
            return False

        # Get release information
        print("📡 Fetching latest release information...")
        try:
            release_info = get_latest_release_info(GITHUB_REPO)
            version = self.version or release_info["version"]
            print(f"✓ Found version: {version}")
            print(f"   Release: {release_info['name']}\n")
        except Exception as e:
            print(f"\n❌ {e}\n")
            return False

        # Find .deb file
        print("🔍 Locating installation package...")
        try:
            download_url, filename = find_deb_asset(release_info["assets"], version)
            print(f"✓ Found: {filename}\n")
        except Exception as e:
            print(f"\n❌ {e}\n")
            return False

        # Download .deb
        print("⬇️  Downloading package...")
        temp_dir = tempfile.mkdtemp()
        deb_path = os.path.join(temp_dir, filename)

        def download_progress(percent, downloaded, total):
            mb_downloaded = downloaded / (1024 * 1024)
            mb_total = total / (1024 * 1024)
            self.print_progress_bar(
                percent,
                prefix="   Progress:",
                suffix=f"{mb_downloaded:.1f}/{mb_total:.1f} MB",
            )

        try:
            download_file(download_url, deb_path, download_progress)
            print("\n✓ Download complete\n")
        except Exception as e:
            print(f"\n❌ {e}\n")
            shutil.rmtree(temp_dir, ignore_errors=True)
            return False

        # Install package
        print("📦 Installing KdG Kiosk...")

        def install_progress(message):
            print(f"   {message}")

        try:
            success, output = install_deb(deb_path, install_progress)
            if success:
                print("\n✅ Installation completed successfully!\n")
            else:
                print(f"\n❌ Installation failed\n")
                return False
        except Exception as e:
            print(f"\n❌ {e}\n")
            shutil.rmtree(temp_dir, ignore_errors=True)
            return False
        finally:
            # Cleanup
            shutil.rmtree(temp_dir, ignore_errors=True)

        # Ask to run setup wizard
        print("=" * 60)
        response = input("\nWould you like to run the setup wizard now? [Y/n]: ")
        if response.lower() != "n":
            print("\n🚀 Launching setup wizard...\n")
            try:
                subprocess.Popen(["python3", "/usr/share/kdg-kiosk/setup_wizard.py"])
            except Exception as e:
                print(f"⚠️  Could not launch setup wizard: {e}")
                print("   You can run it manually with: kdg-kiosk-setup")

        return True


# ============================================================================
# GUI Interface
# ============================================================================

if GUI_AVAILABLE:

    class DownloadThread(QThread):
        """Thread for downloading files"""

        progress = pyqtSignal(int, int, int)  # percent, downloaded, total
        finished = pyqtSignal(bool, str)  # success, message

        def __init__(self, url, dest_path):
            super().__init__()
            self.url = url
            self.dest_path = dest_path

        def run(self):
            try:

                def progress_callback(percent, downloaded, total):
                    self.progress.emit(percent, downloaded, total)

                download_file(self.url, self.dest_path, progress_callback)
                self.finished.emit(True, "Download completed successfully")
            except Exception as e:
                self.finished.emit(False, str(e))

    class InstallThread(QThread):
        """Thread for installing package"""

        progress = pyqtSignal(str)  # status message
        finished = pyqtSignal(bool, str)  # success, message

        def __init__(self, deb_path):
            super().__init__()
            self.deb_path = deb_path

        def run(self):
            try:

                def progress_callback(message):
                    self.progress.emit(message)

                success, output = install_deb(self.deb_path, progress_callback)
                self.finished.emit(success, output)
            except Exception as e:
                self.finished.emit(False, str(e))

    class InstallerWindow(QDialog):
        """GUI installer window"""

        def __init__(self, version=None):
            super().__init__()
            self.version = version
            self.temp_dir = None
            self.deb_path = None
            self.init_ui()
            self.check_and_start()

        def init_ui(self):
            """Initialize UI"""
            self.setWindowTitle("KdG Kiosk Installer")
            self.setMinimumWidth(500)
            self.setMinimumHeight(400)

            layout = QVBoxLayout()

            # Title
            title = QLabel("KdG Kiosk Installer")
            title_font = QFont()
            title_font.setPointSize(16)
            title_font.setBold(True)
            title.setFont(title_font)
            title.setAlignment(Qt.AlignCenter)
            layout.addWidget(title)

            # Status label
            self.status_label = QLabel("Initializing...")
            self.status_label.setAlignment(Qt.AlignCenter)
            layout.addWidget(self.status_label)

            # Progress bar
            self.progress_bar = QProgressBar()
            self.progress_bar.setRange(0, 100)
            layout.addWidget(self.progress_bar)

            # Details text
            self.details_text = QTextEdit()
            self.details_text.setReadOnly(True)
            self.details_text.setMaximumHeight(200)
            layout.addWidget(self.details_text)

            # Buttons
            self.launch_button = QPushButton("Launch Setup Wizard")
            self.launch_button.setEnabled(False)
            self.launch_button.clicked.connect(self.launch_wizard)
            layout.addWidget(self.launch_button)

            self.close_button = QPushButton("Close")
            self.close_button.clicked.connect(self.close)
            layout.addWidget(self.close_button)

            self.setLayout(layout)

        def add_detail(self, message):
            """Add message to details"""
            self.details_text.append(message)

        def check_and_start(self):
            """Check system and start installation"""
            # Check system
            self.status_label.setText("Checking system compatibility...")
            self.add_detail("⚙️ Checking system compatibility...")

            errors = check_system_compatibility()
            if errors:
                error_msg = "System compatibility check failed:\n\n" + "\n".join(
                    f"• {e}" for e in errors
                )
                QMessageBox.critical(self, "Compatibility Error", error_msg)
                self.add_detail("❌ " + error_msg)
                return

            self.add_detail("✓ System compatible")

            # Check root
            if not check_root():
                QMessageBox.warning(
                    self,
                    "Sudo Required",
                    "This installer requires sudo privileges.\n\n"
                    "Please run with: sudo python3 install-kdg-kiosk.py",
                )
                self.add_detail("⚠️ Sudo privileges required")
                return

            # Start installation
            self.start_installation()

        def start_installation(self):
            """Start the installation process"""
            self.status_label.setText("Fetching release information...")
            self.add_detail("\n📡 Fetching latest release from GitHub...")

            try:
                release_info = get_latest_release_info(GITHUB_REPO)
                version = self.version or release_info["version"]
                self.add_detail(f"✓ Found version: {version}")
                self.add_detail(f"   Release: {release_info['name']}")

                download_url, filename = find_deb_asset(release_info["assets"], version)
                self.add_detail(f"✓ Package: {filename}")

                # Start download
                self.download_package(download_url, filename)

            except Exception as e:
                QMessageBox.critical(self, "Error", str(e))
                self.add_detail(f"❌ {e}")

        def download_package(self, url, filename):
            """Download the .deb package"""
            self.status_label.setText("Downloading package...")
            self.add_detail("\n⬇️ Downloading package...")

            self.temp_dir = tempfile.mkdtemp()
            self.deb_path = os.path.join(self.temp_dir, filename)

            self.download_thread = DownloadThread(url, self.deb_path)
            self.download_thread.progress.connect(self.on_download_progress)
            self.download_thread.finished.connect(self.on_download_finished)
            self.download_thread.start()

        def on_download_progress(self, percent, downloaded, total):
            """Handle download progress"""
            self.progress_bar.setValue(percent)
            mb_downloaded = downloaded / (1024 * 1024)
            mb_total = total / (1024 * 1024)
            self.status_label.setText(
                f"Downloading... {mb_downloaded:.1f}/{mb_total:.1f} MB ({percent}%)"
            )

        def on_download_finished(self, success, message):
            """Handle download completion"""
            if success:
                self.add_detail("✓ Download complete")
                self.install_package()
            else:
                QMessageBox.critical(self, "Download Failed", message)
                self.add_detail(f"❌ {message}")
                self.cleanup()

        def install_package(self):
            """Install the package"""
            self.status_label.setText("Installing KdG Kiosk...")
            self.add_detail("\n📦 Installing package...")
            self.progress_bar.setRange(0, 0)  # Indeterminate

            self.install_thread = InstallThread(self.deb_path)
            self.install_thread.progress.connect(self.on_install_progress)
            self.install_thread.finished.connect(self.on_install_finished)
            self.install_thread.start()

        def on_install_progress(self, message):
            """Handle installation progress"""
            self.add_detail(f"   {message}")

        def on_install_finished(self, success, message):
            """Handle installation completion"""
            self.progress_bar.setRange(0, 100)
            self.progress_bar.setValue(100)

            if success:
                self.status_label.setText("✅ Installation completed successfully!")
                self.add_detail("\n✅ Installation completed successfully!")
                self.launch_button.setEnabled(True)
                QMessageBox.information(
                    self,
                    "Success",
                    "KdG Kiosk has been installed successfully!\n\n"
                    "Click 'Launch Setup Wizard' to configure your kiosk.",
                )
            else:
                self.status_label.setText("❌ Installation failed")
                self.add_detail(f"\n❌ Installation failed:\n{message}")
                QMessageBox.critical(self, "Installation Failed", message)

            self.cleanup()

        def launch_wizard(self):
            """Launch the setup wizard"""
            try:
                subprocess.Popen(["python3", "/usr/share/kdg-kiosk/setup_wizard.py"])
                self.close()
            except Exception as e:
                QMessageBox.warning(
                    self,
                    "Error",
                    f"Could not launch setup wizard: {e}\n\n"
                    "You can run it manually with: kdg-kiosk-setup",
                )

        def cleanup(self):
            """Clean up temporary files"""
            if self.temp_dir and os.path.exists(self.temp_dir):
                shutil.rmtree(self.temp_dir, ignore_errors=True)

        def closeEvent(self, event):
            """Handle window close"""
            self.cleanup()
            event.accept()


# ============================================================================
# Main
# ============================================================================


def main():
    parser = argparse.ArgumentParser(
        description="KdG Kiosk Installer - Download and install KdG Kiosk from GitHub Releases"
    )
    parser.add_argument("--cli", action="store_true", help="Force CLI mode (no GUI)")
    parser.add_argument(
        "--version", type=str, help="Specific version to install (default: latest)"
    )

    args = parser.parse_args()

    # Decide whether to use GUI or CLI
    use_gui = GUI_AVAILABLE and not args.cli and os.environ.get("DISPLAY")

    if use_gui:
        app = QApplication(sys.argv)
        installer = InstallerWindow(version=args.version)
        installer.show()
        sys.exit(app.exec_())
    else:
        if not args.cli and GUI_AVAILABLE:
            print("⚠️  No DISPLAY found, falling back to CLI mode\n")
        elif not GUI_AVAILABLE:
            print("⚠️  PyQt5 not available, using CLI mode\n")

        installer = CLIInstaller(version=args.version)
        success = installer.run()
        sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
