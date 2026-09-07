#!/bin/bash

curl -L https://github.com/vmware-tanzu/velero/releases/download/v1.15.0/velero-v1.15.0-linux-amd64.tar.gz -o /tmp/velero-v1.15.0-linux-amd64.tar.gz
cd /tmp
tar -xzvf velero-v1.15.0-linux-amd64.tar.gz
cd velero-v1.15.0-linux-amd64
sudo mv velero /usr/local/bin/

velero version
