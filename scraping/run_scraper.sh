#!/bin/bash
#
# EcommerceFuel Forum Scraper Runner
# Comprehensive script to manage the scraping process
#

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Script directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

# Function to print colored output
print_color() {
    echo -e "${2}${1}${NC}"
}

# Function to check dependencies
check_dependencies() {
    print_color "Checking dependencies..." "$BLUE"
    
    # Check Python
    if ! command -v python3 &> /dev/null; then
        print_color "Python 3 is required but not installed." "$RED"
        exit 1
    fi
    
    # Check if virtual environment exists
    if [ ! -d "venv" ]; then
        print_color "Creating virtual environment..." "$YELLOW"
        python3 -m venv venv
    fi
    
    # Activate virtual environment
    source venv/bin/activate
    
    # Install requirements
    print_color "Installing/updating requirements..." "$YELLOW"
    pip install -q --upgrade pip
    pip install -q -r requirements_scraper.txt
    
    # Install Playwright browsers
    print_color "Setting up Playwright browsers..." "$YELLOW"
    playwright install chromium
    
    print_color "Dependencies ready!" "$GREEN"
}

# Function to show menu
show_menu() {
    echo
    print_color "=== EcommerceFuel Forum Scraper ===" "$BLUE"
    echo
    echo "1) Start scraper (with monitor in new terminal)"
    echo "2) Start scraper only"
    echo "3) Start monitor only"
    echo "4) Resume previous scraping session"
    echo "5) Reset and start fresh"
    echo "6) View scraping statistics"
    echo "7) Open screenshots folder"
    echo "8) Open data folder"
    echo "9) Setup/check dependencies"
    echo "0) Exit"
    echo
    read -p "Select option: " choice
}

# Function to start scraper with monitor
start_with_monitor() {
    print_color "Starting scraper with monitor..." "$GREEN"
    
    # Start monitor in new terminal (macOS)
    if [[ "$OSTYPE" == "darwin"* ]]; then
        osascript -e 'tell app "Terminal" to do script "cd \"'$SCRIPT_DIR'\" && source venv/bin/activate && python scraper_monitor.py"'
    else
        # Linux - try common terminal emulators
        if command -v gnome-terminal &> /dev/null; then
            gnome-terminal -- bash -c "cd $SCRIPT_DIR && source venv/bin/activate && python scraper_monitor.py; read"
        elif command -v xterm &> /dev/null; then
            xterm -e bash -c "cd $SCRIPT_DIR && source venv/bin/activate && python scraper_monitor.py; read" &
        else
            print_color "Could not open new terminal. Run monitor manually: python scraper_monitor.py" "$YELLOW"
        fi
    fi
    
    # Give monitor time to start
    sleep 2
    
    # Start scraper
    python scraper_enhanced.py "$@"
}

# Function to show statistics
show_stats() {
    print_color "Scraping Statistics" "$BLUE"
    echo "=================="
    
    if [ -f "forum_data/scraping_summary.json" ]; then
        python -c "
import json
with open('forum_data/scraping_summary.json', 'r') as f:
    data = json.load(f)
    print(f\"Total posts scraped: {data.get('total_posts_scraped', 0)}\")
    print(f\"Failed URLs: {data.get('failed_urls', 0)}\")
    print(f\"Last run: {data.get('last_run', 'Never')}\")
"
    else
        print_color "No statistics available yet." "$YELLOW"
    fi
    
    # Count files
    if [ -d "forum_data" ]; then
        post_count=$(find forum_data -name "*.json" -not -name "scraping_summary.json" | wc -l)
        print_color "\nPost files in data directory: $post_count" "$GREEN"
    fi
    
    if [ -d "screenshots" ]; then
        screenshot_count=$(find screenshots -name "*.png" | wc -l)
        print_color "Screenshots taken: $screenshot_count" "$GREEN"
    fi
}

# Main loop
while true; do
    show_menu
    
    case $choice in
        1)
            check_dependencies
            start_with_monitor
            ;;
        2)
            check_dependencies
            print_color "Starting scraper..." "$GREEN"
            python scraper_enhanced.py
            ;;
        3)
            check_dependencies
            print_color "Starting monitor..." "$GREEN"
            python scraper_monitor.py
            ;;
        4)
            check_dependencies
            print_color "Resuming previous session..." "$GREEN"
            python scraper_enhanced.py
            ;;
        5)
            check_dependencies
            print_color "Resetting progress..." "$YELLOW"
            read -p "Are you sure you want to reset? (y/N): " confirm
            if [[ $confirm == "y" || $confirm == "Y" ]]; then
                python scraper_enhanced.py --reset
            fi
            ;;
        6)
            show_stats
            read -p "Press Enter to continue..."
            ;;
        7)
            if [[ "$OSTYPE" == "darwin"* ]]; then
                open screenshots
            else
                xdg-open screenshots 2>/dev/null || print_color "Screenshots folder: $SCRIPT_DIR/screenshots" "$BLUE"
            fi
            ;;
        8)
            if [[ "$OSTYPE" == "darwin"* ]]; then
                open forum_data
            else
                xdg-open forum_data 2>/dev/null || print_color "Data folder: $SCRIPT_DIR/forum_data" "$BLUE"
            fi
            ;;
        9)
            check_dependencies
            read -p "Press Enter to continue..."
            ;;
        0)
            print_color "Goodbye!" "$GREEN"
            exit 0
            ;;
        *)
            print_color "Invalid option" "$RED"
            ;;
    esac
done