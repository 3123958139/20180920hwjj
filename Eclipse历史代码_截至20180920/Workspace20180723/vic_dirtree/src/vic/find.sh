#!/bin/bash


find ./ -name "*" -type f -maxdepth 4| xargs grep $1
