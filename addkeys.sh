#!/bin/bash
# Description: Add SSH private keys to the SSH agent
# Sets proper permissions on SSH keys and adds them to the SSH agent
chmod 600 ~/.ssh/*
ssh-add ~/.ssh/pkkid-rsa
ssh-add ~/.ssh/nasuni-internal
ssh-add ~/.ssh/nasuni-support
