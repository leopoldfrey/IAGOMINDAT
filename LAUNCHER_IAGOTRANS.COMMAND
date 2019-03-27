#!/bin/sh
echo Starting IAGOMINDAT
cd $(dirname $0)/src
python3 -W ignore ./MindatSearch.py
echo Done