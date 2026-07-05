# Cronix
# 🚀 Cronix Browser Installation Guide

This guide will walk you through installing the Cronix Browser on your Linux system. We provide an automated installation script that checks dependencies, logs you into GitHub CLI if needed, downloads the latest release, and installs the application cleanly.

## 📋 Prerequisites

Before running the installation, ensure you have:
* An active internet connection.
* **Sudo/Administrator** privileges on your machine.
* A GitHub account (the script uses the GitHub CLI to safely fetch the latest release).

---


## 🛠️ Installation

To install Cronix Browser, follow these steps:

### Step 1: Download the installer script
```bash
git clone https://github.com/james15-spec/Cronix-browser.git
cd Cronix-Browser
```

### Step 2: Make the script executable
By default, downloaded scripts lack execution permissions. Enable them by running:
```bash
chmod +x install.sh
```

### Step 3: Run the installer
Execute the script to start the installation process:
```bash
./install.sh
```

---

## 🔄 What the Installer Does Automatically

1. **GitHub CLI Verification:** Checks if you are authenticated with `gh`. If not, it safely prompts you to log in.
2. **Dependency Management:** Automatically updates your package lists and installs required system dependencies (`python3`, `pip`, `python3-venv`, and `gh`).
3. **Clean Up:** Automatically locates and removes any outdated `.deb` install files from your directory.
4. **Targeted Download:** Fetches the absolute newest release file from the repository.
5. **System Installation:** Installs the `.deb` package using your native system package manager (`apt`).
6. **Silent Launch:** Starts Cronix Browser immediately while suppressing noisy backend graphical terminal logs.

---

## 🏃 Running Cronix Browser

Once installed, you can launch the browser anytime by simply typing its name in your terminal:
```bash
cronix
```
*(All unnecessary warning messages and background debug logs are filtered out automatically for a clean terminal experience!)*

