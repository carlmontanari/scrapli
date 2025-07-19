Value HOSTNAME (\S+)
Value CHASSIS_TYPE (.+)

Start
  ^Hostname\s+:\s+${HOSTNAME}
  ^Chassis\s+Type\s+:\s+${CHASSIS_TYPE} -> Record
