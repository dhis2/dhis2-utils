#!/bin/bash

# Installs YourKit Java Profiler
# Run as root with 'sudo ./install_yjp.sh'
#
# Enable with:
# JAVA_OPTS="$JAVA_OPTS -agentpath:/path/to/libyjpagent.so"

YJP_URL="https://s3-eu-west-1.amazonaws.com/content.dhis2.org/development/yjp/yjp.zip" 
YJP_FILE="yjp.zip"
INSTALL_DIR="/var/lib"
AGENT_FILE="${INSTALL_DIR}/yjp/bin/linux-x86-64/libyjpagent.so"
TOMCAT_CONF_DIR="/etc/tomcat/conf.d"
TOMCAT_CONF_FILE="${TOMCAT_CONF_DIR}/yjp.conf"

echo "Dowloading YourKit archive.."

rm -f ${YJP_FILE}
rm -rf /tmp/yjp

wget ${YJP_URL}

if [ -f "${YJP_FILE}" ]; then
  echo "Downloaded file: ${YJP_FILE}"
else
  echo "File not found: ${YJP_URL}"
  exit 1
fi

echo "Extracting archive.."

unzip -q ${YJP_FILE} -d /tmp

echo "Installing YourKit.."

chown root:root /tmp/yjp -R
mv /tmp/yjp ${INSTALL_DIR}

if [ -f "${AGENT_FILE}" ]; then
  echo "Agent installed: ${AGENT_FILE}"
else
  echo "Could not install agent"
  exit 1
fi

echo "Enabling agent.."

if [ -d "${TOMCAT_CONF_DIR}" ]; then
  echo "JAVA_OPTS=\"\$JAVA_OPTS -agentpath:${AGENT_FILE}\"" > ${TOMCAT_CONF_FILE}

  if [ -f "${TOMCAT_CONF_FILE}" ]; then
    echo "Tomcat conf file created: ${TOMCAT_CONF_FILE}"
  else
    echo "Tomcat conf file could not be created"
  fi
else
  echo "Could not install Tomcat config, install manuall by adding to JAVA_OPTS:"
  echo "-agentpath:${AGENT_FILE}"
fi

echo "Installation done"
echo ""
