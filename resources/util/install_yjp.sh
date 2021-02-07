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
  echo "Agent successfully installed at: ${AGENT_FILE}"
  echo "Enable agent by adding to JAVA_OPTS:"
  echo "-agentpath:${AGENT_FILE}"
else
  echo "Installation failed"
  exit 1
fi

echo ""
