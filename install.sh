#!/bin/sh
# fields
RED='\033[0;31m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color
GREEN='\033[0;32m'
YELLOW='\033[0;33m'

# Package list
echo "[COLIOT] ${CYAN}Updating packages..${NC}"
apt-get update

# Install dependencies Debian and Ubuntu
echo "[COLIOT] ${CYAN}Installing dependecies..${NC}"
apt-get install build-essential libssl-dev libffi-dev python3-dev python3-pip libsasl2-dev libldap2-dev -y
# Ubuntu 16.04 LTS -add python3.5-dev

# Install SQLite3
apt-get install sqlite3

apt-get install mysql-server -y

# Check distribution
echo "[COLIOT] ${CYAN}Checking distribution..${NC}"
DEBIAN=$(cat /proc/version | grep "debian")
UBUNTU=$(cat /proc/version | grep "ubuntu")
if [ ! -z  "$DEBIAN" ]; then
	echo "[COLIOT] ${GREEN}Debian detected..${NC}"
	apt-get install curl software-properties-common -y
	curl -sL https://deb.nodesource.com/setup_11.x | bash -
	apt-get install nodejs -y
	apt-get install default-libmysqlclient-dev -y
elif [ ! -z "$UBUNTU" ]; then
	echo "[COLIOT] ${GREEN}Ubuntu detected..${NC}"
	apt-get install libmysqlclient-dev -y
	apt-get install nodejs npm -y
else
	echo "[COLIOT] ${YELLOW}Warning: Unsupported distribution.${NC}"
	apt-get install libmysqlclient-dev -y
        apt-get install nodejs npm -y
fi
# Python’s setup tools and pip
pip3 install --user --upgrade setuptools

pip3 install python-dotenv

pip3 install click==6.7

pip3 install markdown==2.6.11

# Superset installation and initialization

# Create directory
echo "[COLIOT] ${CYAN}Creating /opt/coliot directory..${NC}"
mkdir -p /opt/coliot

echo "[COLIOT] ${CYAN}Cloning into /opt/coliot/..${NC}"
git clone https://github.com/apache/incubator-superset.git -b 0.26.0 /opt/coliot/

rm -R /opt/coliot/superset
cp -R ./collector /opt/coliot/superset

echo "[COLIOT] ${CYAN}Cloning and installing Coliot modul..${NC}"
git clone https://github.com/gre0071/coliot-modul.git /opt/coliot/coliot-modul
echo '[SQLITE]
database = /opt/coliot/superset/db_coliot/coliot.db' > /opt/coliot/coliot-modul/coliot.conf
echo "[COLIOT] ${GREEN}Success..${NC}"


# Install external dependencies
echo "[COLIOT] ${CYAN}Installing external dependencies..${NC}"
pip3 install -r /opt/coliot/requirements.txt
pip3 install -r /opt/coliot/requirements-dev.txt
pip3 install psycopg2-binary

# Install Superset in editable (development) mode
echo "[COLIOT] ${CYAN}Installing Coliot..${NC}"
pip3 install -e /opt/coliot/.

# Create an admin user
echo "[COLIOT] ${CYAN}Creating an admin user..${NC}"
echo "[COLIOT] ${YELLOW}Please fill out the following information. This information will be used to log in to the Coliot.${NC}"
fabmanager create-admin --app superset

# Initialize the database
echo "[COLIOT] ${CYAN}Initializing the database..${NC}"
superset db upgrade

# Create default roles and permissions
echo "[COLIOT] ${CYAN}Creating default roles and permissions..${NC}"
superset init

# Load data to DB
echo "[COLIOT] ${CYAN}Loading data to database..${NC}"
. /opt/coliot/superset/db_coliot/load_data.sh

echo "[COLIOT] ${CYAN}Creating Coliot service..${NC}"
echo '[Unit]
Description=COLIOT service
After=network.target
StartLimitIntervalSec=0

[Service]
Type=simple
Restart=always
RestartSec=1
User=root
ExecStart=/usr/bin/env superset runserver -d -p 8088

[Install]
WantedBy=multi-user.target' > /etc/systemd/system/coliot.service

echo "[COLIOT] ${CYAN}Restarting Coliot service..${NC}"
systemctl daemon-reload
systemctl stop coliot
systemctl start coliot

echo "[COLIOT] ${GREEN}Coliot service is now running on 0.0.0.0:8088${NC}"

echo "${CYAN}

         CCCCCCCCCCCCC     OOOOOOOOO     LLLLLLLLLLL         IIIIIIIIII     OOOOOOOOO     TTTTTTTTTTTTTTTTTTTTTTT
     CCC::::::::::::C   OO:::::::::OO   L:::::::::L         I::::::::I   OO:::::::::OO   T:::::::::::::::::::::T
   CC:::::::::::::::C OO:::::::::::::OO L:::::::::L         I::::::::I OO:::::::::::::OO T:::::::::::::::::::::T
  C:::::CCCCCCCC::::CO:::::::OOO:::::::OLL:::::::LL         II::::::IIO:::::::OOO:::::::OT:::::TT:::::::TT:::::T
 C:::::C       CCCCCCO::::::O   O::::::O  L:::::L             I::::I  O::::::O   O::::::OTTTTTT  T:::::T  TTTTTT
C:::::C              O:::::O     O:::::O  L:::::L             I::::I  O:::::O     O:::::O        T:::::T
C:::::C              O:::::O     O:::::O  L:::::L             I::::I  O:::::O     O:::::O        T:::::T
C:::::C              O:::::O     O:::::O  L:::::L             I::::I  O:::::O     O:::::O        T:::::T
C:::::C              O:::::O     O:::::O  L:::::L             I::::I  O:::::O     O:::::O        T:::::T
C:::::C              O:::::O     O:::::O  L:::::L             I::::I  O:::::O     O:::::O        T:::::T
C:::::C              O:::::O     O:::::O  L:::::L             I::::I  O:::::O     O:::::O        T:::::T
 C:::::C       CCCCCCO::::::O   O::::::O  L:::::L     LLLLLL  I::::I  O::::::O   O::::::O        T:::::T
  C:::::CCCCCCCC::::CO:::::::OOO:::::::OLL:::::::LLLLL:::::LII::::::IIO:::::::OOO:::::::O      TT:::::::TT
   CC:::::::::::::::C OO:::::::::::::OO L::::::::::::::::::LI::::::::I OO:::::::::::::OO       T:::::::::T
     CCC::::::::::::C   OO:::::::::OO   L::::::::::::::::::LI::::::::I   OO:::::::::OO         T:::::::::T
        CCCCCCCCCCCCC     OOOOOOOOO     LLLLLLLLLLLLLLLLLLLLIIIIIIIIII     OOOOOOOOO           TTTTTTTTTTT

${NC}"
