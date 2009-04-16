#! /bin/sh
killall syncml-ds-tool
syncml-ds-tool --http-server 1234 --sync $1 $2 $3
syncml-ds-tool --http-server 1234 --sync $1 $2 $3
