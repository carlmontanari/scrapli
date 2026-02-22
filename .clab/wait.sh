#!/bin/bash
MAX_TIME=300
INTERVAL=5
END_TIME=$((SECONDS + MAX_TIME))

while [ $SECONDS -lt $END_TIME ]; do
    echo "waiting for srl ssh..."
    # ensure srl is up and running and displays the normal banner (is past the initial boot stuff
    # basically where it is only basic cli)
    sshpass -p "NokiaSrl1!" \
      ssh -o ConnectTimeout=5 -o StrictHostKeyChecking=no -l admin 172.20.20.16 quit  2>&1 \
      | grep "Welcome to Nokia SR Linux"

    if [ $? -eq 0 ]; then
        echo "srl ssh available..."
        break
    fi

    sleep $INTERVAL
done

while [ $SECONDS -lt $END_TIME ]; do
    echo "waiting for srl netconf..."
    # same thing for netconf port just to be safe!
    sshpass -p "NokiaSrl1!" \
      ssh -o ConnectTimeout=5 -o StrictHostKeyChecking=no -l admin -p 830 172.20.20.16 quit  2>&1 \
      | grep "Welcome to Nokia SR Linux"

    if [ $? -eq 0 ]; then
        echo "srl netconf available..."
        break
    fi

    sleep $INTERVAL
done

while [ $SECONDS -lt $END_TIME ]; do
    echo "waiting for netopeer netconf..."
    # and lastly for netopeer
    (
      echo '<?xml version="1.0" encoding="UTF-8"?>'
      echo '<hello xmlns="urn:ietf:params:xml:ns:netconf:base:1.0">'
      echo '  <capabilities>'
      echo '    <capability>urn:ietf:params:netconf:base:1.0</capability>'
      echo '  </capabilities>'
      echo '</hello>'
      echo ']]>]]>'
      sleep 1
    ) \
      | sshpass -p "password" \
      ssh -o ConnectTimeout=5 -o StrictHostKeyChecking=no -l root -p 830 172.20.20.18 -s netconf  2>&1 \
      | grep "<hello"

    if [ $? -eq 0 ]; then
        echo "netopeer netconf available..."
        exit 0
    fi

    sleep $INTERVAL
done

exit 1
