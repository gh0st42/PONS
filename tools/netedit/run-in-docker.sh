#!/bin/sh

docker run --rm -it -p 6080:6080 -p 5901:5901 --name netedit -v $(pwd):/shared gh0st42/netedit
