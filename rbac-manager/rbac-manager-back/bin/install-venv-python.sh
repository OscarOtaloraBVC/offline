#!/bin/bash
PATHENV=/opt/rbac-manager/backend/venv
#PATHREQUERIMENTS=/opt/rbac-manager/backend/bin/requirements.txt
PATHREQUERIMENTS=/opt/rbac-manager/backend/requirements.txt 

sudo apt install python3-pip
sudo apt install python3.12-venv

python3 -m venv $PATHENV

source $PATHENV/bin/activate

pip3 install -r "$PATHREQUERIMENTS"

deactivate
