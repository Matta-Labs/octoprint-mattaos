#!/bin/bash

# Load arguments
LATEST_RELEASE_TAG=$1
URL=$2

# Color codes
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m'  # No Color

# Function to echo colored text
function color_echo {
    local message="$1"
    echo -e "${BLUE}${message}${NC}"
}

function error_echo {
    local message="$1"
    echo -e "${RED}${message}${NC}"
}

color_echo "Initiating installation of octoprint-mattaos..."
color_echo "Latest release tag is: $LATEST_RELEASE_TAG"
color_echo "URL is: $URL"
# Debug:
echo -e "User is: $USER"

# Install required packages

ENV_NAME="oprint"

# Set up virtual environment
color_echo "Activating virtual environment..."
source ~/$ENV_NAME/bin/activate

# Install the plugin from GitHub
# pip install -e .
color_echo "Installing octoprint-mattaos from GitHub..."

color_echo "Latest release tag is: $LATEST_RELEASE_TAG"
# Install the plugin from GitHub at the latest release
pip install git+https://github.com/Matta-Labs/octoprint-mattaos@$LATEST_RELEASE_TAG#egg=octoprint-mattaconnect

if [ $? -eq 0 ]; then
    color_echo "Installation completed!"
else
    error_echo "Installation failed!"
    exit 1
fi