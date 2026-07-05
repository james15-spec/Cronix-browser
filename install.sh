#!/bin/bash
KEYWORD="cronix"
DIRECTORY="$(pwd)"
echo "Hello! This is the Cronix Browser install!."
echo "Thank you for installing!."
APP="cronix"

run_cronix_silently() {
    export QT_LOGGING_RULES="*.debug=false;qt.webenginecontext.info=false;qt.webenginecontext.warning=false"
    export MESA_DEBUG=0
    export EGL_LOG_LEVEL=fatal
    cronix > /dev/null 2>&1 &
}


check_github_login() {
    if ! gh auth status >/dev/null 2>&1; then
        echo "Please log in to continue the download:"
        gh auth login
    fi
}

OLD_DEB_FILE=$(find "$DIRECTORY" -maxdepth 1 -type f -name "*$KEYWORD*.deb" | head -n 1)
rm -f "$OLD_DEB_FILE"

if command -v "$APP" >/dev/null 2>&1; then
    echo "✅ Cronix is already installed! Running Cronix Browser..."
    run_cronix_silently
    exit 0
else
    echo "❌ Cronix is not installed. Proceeding..."

    echo "Checking Dependencies..."
    sudo apt update
    sudo apt install -y python3 python3-pip python3-venv gh
    echo "Dependencies installed! Logging you in to Github!"
    check_github_login
    echo "Checks done! Proceeding..."
    echo "Downloading..."
    gh release download --repo "james15-spec/Cronix-browser" -D "$DIRECTORY"
    
    echo "Installing..."
    DEB_FILE=$(find "$DIRECTORY" -maxdepth 1 -type f -name "*$KEYWORD*.deb" | head -n 1)
    
    if [ -z "$DEB_FILE" ]; then
        echo "Error: No .deb file found matching '$KEYWORD'"
        exit 1
    fi

    sudo apt install -y "$DEB_FILE"
    echo "Done! Running Cronix..."
    run_cronix_silently
fi
