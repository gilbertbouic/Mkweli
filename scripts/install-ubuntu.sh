#!/bin/bash
#
# Mkweli AML - Ubuntu Installation Script
# This script automatically installs Mkweli AML on Ubuntu systems.
#
# Usage: curl -fsSL https://raw.githubusercontent.com/gilbertbouic/Mkweli/main/scripts/install-ubuntu.sh | bash
#
# Requirements:
#   - Ubuntu 20.04 or newer
#   - Internet connection
#   - sudo privileges
#

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Print colored output
print_status() {
    echo -e "${BLUE}[*]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[✓]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[!]${NC} $1"
}

print_error() {
    echo -e "${RED}[✗]${NC} $1"
}

# Print banner
print_banner() {
    echo ""
    echo -e "${GREEN}╔═══════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${GREEN}║                                                               ║${NC}"
    echo -e "${GREEN}║${NC}        ${BLUE}Mkweli AML - Sanctions Screening Tool${NC}                 ${GREEN}║${NC}"
    echo -e "${GREEN}║${NC}        ${YELLOW}Ubuntu Installation Script${NC}                           ${GREEN}║${NC}"
    echo -e "${GREEN}║                                                               ║${NC}"
    echo -e "${GREEN}╚═══════════════════════════════════════════════════════════════╝${NC}"
    echo ""
}

# Check if running on Ubuntu/Debian
check_os() {
    print_status "Checking operating system..."
    if [ -f /etc/os-release ]; then
        . /etc/os-release
        if [[ "$ID" != "ubuntu" && "$ID" != "debian" && "$ID_LIKE" != *"ubuntu"* && "$ID_LIKE" != *"debian"* ]]; then
            print_warning "This script is designed for Ubuntu/Debian. Your OS: $ID"
            print_warning "Continuing anyway, but some commands may not work."
        else
            print_success "Operating system: $PRETTY_NAME"
        fi
    else
        print_warning "Could not detect operating system. Continuing anyway..."
    fi
}

# Check system requirements
check_requirements() {
    print_status "Checking system requirements..."
    
    # Check RAM
    total_ram=$(free -m | awk '/^Mem:/{print $2}')
    if [ "$total_ram" -lt 2000 ]; then
        print_warning "Warning: Your system has less than 2GB RAM. Mkweli may run slowly."
    else
        print_success "RAM: ${total_ram}MB (minimum 2GB recommended)"
    fi
    
    # Check disk space
    available_space=$(df -m "$HOME" | awk 'NR==2{print $4}')
    if [ "$available_space" -lt 5000 ]; then
        print_warning "Warning: Less than 5GB disk space available. You may run out of space."
    else
        print_success "Available disk space: ${available_space}MB"
    fi
}

# Install Docker if not present
install_docker() {
    print_status "Checking for Docker..."
    
    if command -v docker &> /dev/null; then
        print_success "Docker is already installed"
        docker_version=$(docker --version | cut -d ' ' -f3 | tr -d ',')
        print_success "Docker version: $docker_version"
    else
        print_status "Installing Docker..."
        
        # Update package list
        sudo apt-get update -qq
        
        # Install Docker
        sudo apt-get install -y docker.io
        
        # Start and enable Docker service
        sudo systemctl start docker
        sudo systemctl enable docker
        
        print_success "Docker installed successfully"
    fi
    
    # Check for docker-compose
    print_status "Checking for docker-compose..."
    
    if command -v docker-compose &> /dev/null; then
        print_success "docker-compose is already installed"
    else
        print_status "Installing docker-compose..."
        sudo apt-get install -y docker-compose
        print_success "docker-compose installed successfully"
    fi
}

# Add user to docker group
configure_docker_permissions() {
    print_status "Configuring Docker permissions..."
    
    if groups "$USER" | grep -q docker; then
        print_success "User already in docker group"
    else
        sudo usermod -aG docker "$USER"
        print_success "Added user to docker group"
        print_warning "NOTE: You may need to log out and log back in for this to take effect."
    fi
}

# Clone or update the Mkweli repository
get_mkweli() {
    print_status "Downloading Mkweli AML..."
    
    INSTALL_DIR="$HOME/Mkweli"
    
    if [ -d "$INSTALL_DIR" ]; then
        print_status "Mkweli directory exists. Updating..."
        cd "$INSTALL_DIR"
        git pull origin main || {
            print_warning "Could not update. Using existing installation."
        }
    else
        print_status "Cloning Mkweli repository..."
        git clone https://github.com/gilbertbouic/Mkweli.git "$INSTALL_DIR"
        cd "$INSTALL_DIR"
    fi
    
    print_success "Mkweli downloaded to $INSTALL_DIR"
}

# Create configuration file
create_config() {
    print_status "Creating configuration file..."
    
    cd "$HOME/Mkweli"
    
    if [ ! -f ".env" ]; then
        if [ -f ".env.example" ]; then
            cp .env.example .env
            print_success "Configuration file created"
        else
            print_warning "No .env.example found. Creating basic .env file..."
            echo "PORT=8000" > .env
            echo "FLASK_ENV=production" >> .env
            print_success "Basic configuration file created"
        fi
    else
        print_success "Configuration file already exists"
    fi
}

# Start Mkweli with Docker
start_mkweli() {
    print_status "Starting Mkweli AML..."
    
    cd "$HOME/Mkweli"
    
    # Use sudo for docker-compose if user is not in docker group yet
    if groups "$USER" | grep -q docker; then
        docker-compose up -d
    else
        sudo docker-compose up -d
    fi
    
    print_success "Mkweli AML is starting..."
}

# Create desktop shortcut
create_desktop_shortcut() {
    print_status "Creating desktop shortcut..."
    
    DESKTOP_FILE="$HOME/.local/share/applications/mkweli-aml.desktop"
    mkdir -p "$HOME/.local/share/applications"
    
    cat > "$DESKTOP_FILE" << 'EOF'
[Desktop Entry]
Version=1.0
Type=Application
Name=Mkweli AML
Comment=Sanctions Screening Tool
Exec=xdg-open http://localhost:8000
Icon=web-browser
Terminal=false
Categories=Office;Finance;
Keywords=AML;sanctions;screening;compliance;KYC;
EOF
    
    # Also create shortcut on Desktop if it exists
    if [ -d "$HOME/Desktop" ]; then
        cp "$DESKTOP_FILE" "$HOME/Desktop/mkweli-aml.desktop"
        chmod +x "$HOME/Desktop/mkweli-aml.desktop"
        print_success "Desktop shortcut created"
    fi
    
    # Create start/stop scripts
    cat > "$HOME/Mkweli/start-mkweli.sh" << 'EOF'
#!/bin/bash
cd ~/Mkweli
docker-compose up -d
echo "Mkweli AML started. Open http://localhost:8000 in your browser."
EOF
    chmod +x "$HOME/Mkweli/start-mkweli.sh"
    
    cat > "$HOME/Mkweli/stop-mkweli.sh" << 'EOF'
#!/bin/bash
cd ~/Mkweli
docker-compose down
echo "Mkweli AML stopped."
EOF
    chmod +x "$HOME/Mkweli/stop-mkweli.sh"
    
    print_success "Helper scripts created in $HOME/Mkweli/"
}

# Wait for application to be ready
wait_for_app() {
    print_status "Waiting for application to start (this may take 1-2 minutes)..."
    
    max_attempts=60
    attempt=0
    
    while [ $attempt -lt $max_attempts ]; do
        if curl -s http://localhost:8000 > /dev/null 2>&1; then
            print_success "Mkweli AML is ready!"
            return 0
        fi
        attempt=$((attempt + 1))
        sleep 2
        echo -n "."
    done
    
    echo ""
    print_warning "Application is still starting. Please wait a moment and try accessing http://localhost:8000"
}

# Print success message with next steps
print_final_message() {
    echo ""
    echo -e "${GREEN}╔═══════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${GREEN}║                                                               ║${NC}"
    echo -e "${GREEN}║${NC}              ${GREEN}✓ Installation Complete!${NC}                        ${GREEN}║${NC}"
    echo -e "${GREEN}║                                                               ║${NC}"
    echo -e "${GREEN}╚═══════════════════════════════════════════════════════════════╝${NC}"
    echo ""
    echo -e "${BLUE}Next Steps:${NC}"
    echo ""
    echo -e "  1. Open your browser and go to: ${YELLOW}http://localhost:8000${NC}"
    echo ""
    echo -e "  2. Log in with:"
    echo -e "     Username: ${YELLOW}admin${NC}"
    echo -e "     Password: ${YELLOW}admin123${NC}"
    echo ""
    echo -e "  3. ${RED}IMPORTANT: Change your password immediately!${NC}"
    echo -e "     Click ⚙️ → Change Password"
    echo ""
    echo -e "${BLUE}Useful Commands:${NC}"
    echo ""
    echo -e "  Start Mkweli:   ${YELLOW}cd ~/Mkweli && docker-compose up -d${NC}"
    echo -e "  Stop Mkweli:    ${YELLOW}cd ~/Mkweli && docker-compose down${NC}"
    echo -e "  View logs:      ${YELLOW}cd ~/Mkweli && docker-compose logs${NC}"
    echo -e "  Check status:   ${YELLOW}docker ps${NC}"
    echo ""
    echo -e "${BLUE}Need Help?${NC}"
    echo -e "  Email: gilbert@mkweli.tech"
    echo -e "  Docs:  https://mkweli.tech/docs"
    echo ""
    
    # Try to open browser
    if command -v xdg-open &> /dev/null; then
        print_status "Opening browser..."
        xdg-open http://localhost:8000 2>/dev/null || true
    fi
}

# Main installation function
main() {
    print_banner
    
    # Check if running as root (not recommended)
    if [ "$EUID" -eq 0 ]; then
        print_warning "Running as root is not recommended."
        print_warning "Please run as a normal user with sudo privileges."
    fi
    
    # Run installation steps
    check_os
    check_requirements
    
    print_status "Installing prerequisites..."
    sudo apt-get update -qq
    sudo apt-get install -y curl git
    
    install_docker
    configure_docker_permissions
    get_mkweli
    create_config
    start_mkweli
    create_desktop_shortcut
    wait_for_app
    print_final_message
}

# Run main function
main
