#!/bin/bash

# Installs YourKit Java Profiler
#
# Run as root with 'sudo ./install_yjp.sh'
#
# Requires 'unzip'
#
# Enable for Tomcat with:
# JAVA_OPTS="$JAVA_OPTS -agentpath:/path/to/libyjpagent.so"
#
# Manual steps
#
# Download the Linux x64 distribution from https://www.yourkit.com/java/profiler/download/. Note that the URL changes over time.
#
# $ wget https://download.yourkit.com/yjp/2023.9/YourKit-JavaProfiler-2023.9-b103-x64.zip
#
# Unzip the archive.
#
# $ unzip YourKit-JavaProfiler-2023.9-b97-x64.zip
#
# Rename the directory to 'yjp'.
#
# $ mv YourKit-JavaProfiler-2023.9-b97-x64 yjp

YJP_DIR="yjp"
INSTALL_DIR="/var/lib"
AGENT_FILE="${INSTALL_DIR}/yjp/bin/linux-x86-64/libyjpagent.so"
TOMCAT_CONF_DIR="/etc/tomcat/conf.d"
TOMCAT_CONF_FILE="${TOMCAT_CONF_DIR}/yjp.conf"

# Verify YJP

if [ -d "${YJP_DIR}" ]; then
  echo "YJP directory found: ${YJP_DIR}"
else
  echo "YJP directory not found: ${YJP_DIR}"
  exit 1
fi

echo "Installing YourKit.."

chown root:root ${YJP_DIR} -R
mv ${YJP_DIR} ${INSTALL_DIR}

# Verify agent file

if [ -f "${AGENT_FILE}" ]; then
  echo "Agent installed: '${AGENT_FILE}'"
else
  echo "Could not install agent"
  exit 1
fi

echo "Enabling agent.."

if [ -d "${TOMCAT_CONF_DIR}" ]; then
  echo "JAVA_OPTS=\"\$JAVA_OPTS -agentpath:${AGENT_FILE}\"" > ${TOMCAT_CONF_FILE}
  chown root:tomcat ${TOMCAT_CONF_FILE}

  if [ -f "${TOMCAT_CONF_FILE}" ]; then
    echo "Tomcat conf file created: ${TOMCAT_CONF_FILE}"
  else
    echo "Tomcat conf file could not be created"
  fi
else
  echo "Could not install Tomcat config, install manuall by adding to JAVA_OPTS."
  echo "-agentpath:${AGENT_FILE}"
fi

echo "Installation done, restart Tomcat for changes to take effect"
echo ""
