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
    # Added zstd and binutils (provides 'ar') to ensure compression works
    sudo apt install -y python3 python3-pip python3-venv zstd binutils
    echo "Dependencies installed!"
    echo "Checks done! Proceeding..."
    
    echo "Compiling..."
    # 1. Ensure we are exactly in the original directory before navigating
    cd "$DIRECTORY"
    
    # 2. Navigate into the source directory
    cd cronix_1.4.2 || { echo "Error: cronix_1.4.2 folder not found!"; exit 1; }
    rm -f README.md
    
    # 4. Create the final .deb package using 'ar'
    ar rcs "../cronix_1.4.2.deb" debian-binary control.tar.zst data.tar.zst
    
    # 5. Safely return back to the root directory
    cd "$DIRECTORY"
    
    echo "Installing..."
    # Added a tiny pause to make sure the filesystem registers the new file
    sleep 1
    DEB_FILE=$(find "$DIRECTORY" -maxdepth 1 -type f -name "*$KEYWORD*.deb" | head -n 1)
    
    if [ -z "$DEB_FILE" ]; then
        echo "Error: No .deb file found matching '$KEYWORD' in $DIRECTORY"
        exit 1
    fi

    # Using ./ prefix ensures apt recognizes it as a local file pathway
    sudo apt install -y "./$(basename "$DEB_FILE")"
    echo "Done! Running Cronix..."
    run_cronix_silently
fi
