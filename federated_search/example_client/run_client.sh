#!/bin/bash

python -m http.server 5500
open("http://localhost:5500/example.html")