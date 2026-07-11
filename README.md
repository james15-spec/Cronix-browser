# Cronix
# 🚀 Cronix Browser Installation Guide

This guide will walk you through installing the Cronix Browser on your Linux or Windows system. We provide an automated installation script for linux users (for Windows users, we provide a exe installer) that checks dependencies, logs you into GitHub CLI if needed, downloads the latest release, and installs the application cleanly.

## Windows Users

for Windows, extract the cronix-installer.zip and double click(open) the setup exe file.
### Notice
Cronix is currently unsigned, so Windows may show a SmartScreen warning. Click More info → Run anyway to install.

## 📋 Prerequisites

Before running the installation, ensure you have:
* An active internet connection.
* **Sudo/Administrator** privileges on your machine.

---


## 🛠️ Installation For Linux

To install Cronix Browser, follow these steps:

### Step 1: Download the installer script
```bash
git clone https://github.com/james15-spec/Cronix-browser.git
cd Cronix-browser
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


1. **Dependency Management:** Automatically updates your package lists and installs required system dependencies.
2. **Clean Up:** Automatically locates and removes any outdated `.deb` install files from your directory.
3. **Creation** Compiles the compressed source code into a .deb.
4. **System Installation:** Installs the `.deb` package using your native system package manager (`apt`).
5. **Silent Launch:** Starts Cronix Browser immediately while suppressing noisy backend graphical terminal logs.

---


## 🏃 Running Cronix Browser

Once installed, you can launch the browser anytime by simply typing its name in your terminal:
```bash
cronix
```
*(All unnecessary warning messages and background debug logs are filtered out automatically for a clean terminal experience)*

## Any Issues?
if there are any issues or questions, we're happy to help and to try and fix/answer them, just get in touch at:
```mailto
croftonixstudios@outlook.com
```

