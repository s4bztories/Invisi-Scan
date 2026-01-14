#!/bin/bash
clear
echo "====================================================="
echo "      AI ETHICAL HACKING LAB - ONE CLICK MENU"
echo "====================================================="

if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
fi

source venv/bin/activate

echo "Installing modules..."
pip install -r requirements.txt >/dev/null

while true; do
clear
echo "====================================================="
echo "                     MAIN MENU"
echo "====================================================="
echo "1) Fast Scan"
echo "2) Custom Port Scan"
echo "3) Network Device Discovery"
echo "4) Run Dashboard (Flask)"
echo "5) Exit"
echo "====================================================="
read -p "Choose an option: " choice

case $choice in
    1)
        read -p "Enter target (IP or domain): " target
        python3 main.py scan --target "$target" --fast
        read -p "Press Enter to continue..." ;;
    2)
        read -p "Enter target (IP or domain): " target
        read -p "Enter ports (ex: 1-1024 or 22,80,443): " ports
        python3 main.py scan --target "$target" --ports "$ports"
        read -p "Press Enter to continue..." ;;
    3)
        read -p "Enter network range (ex: 192.168.1.0/24): " net
        python3 main.py discover --target "$net"
        read -p "Press Enter to continue..." ;;
    4)
        echo "Starting Flask dashboard..."
        python3 -m webapp.app
        read -p "Press Enter to continue..." ;;
    5)
        echo "Exiting..."
        exit 0 ;;
    *)
        echo "Invalid option!"
        sleep 1 ;;
esac
done
