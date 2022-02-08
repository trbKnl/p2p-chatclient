#!/bin/bash

# Copy all files to the VM for testing
# recursive, preserve modification times, quite
rsync -av --delete -e "ssh" /home/turbo/pythontest/securechat root@192.168.111.101:/root
rsync -av --delete -e "ssh" /home/turbo/pythontest/securechat root@192.168.222.101:/root

echo "done"
