#! /bin/sh
killall syncml-ds-tool
while [ 1 -ne 0 ]
do
  syncml-ds-tool --username test --password test --http-server 1234 --sync $1 $2 $3
done
