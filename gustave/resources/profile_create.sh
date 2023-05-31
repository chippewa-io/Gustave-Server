#!/bin/bash

# Variables
jamfProURL="$1"
jamfProUser="$2"
jamfProPass="$3"
apiEndPoint="JSSResource/osxconfigurationprofiles/id/0" # id/0 to create new profile

# Payload (needs to be escaped)
payloadXML=$(echo '<?xml version="1.0" encoding="UTF-8"?><!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd"><plist version="1"><dict><key>PayloadUUID</key><string>42884445-1B56-4EA4-A3D6-7009702F5CC7</string><key>PayloadType</key><string>Configuration</string><key>PayloadOrganization</key><string>Jamf</string><key>PayloadIdentifier</key><string>42884445-1B56-4EA4-A3D6-7009702F5CC7</string><key>PayloadDisplayName</key><string>'$4'</string><key>PayloadDescription</key><string/><key>PayloadVersion</key><integer>1</integer><key>PayloadEnabled</key><true/><key>PayloadRemovalDisallowed</key><true/><key>PayloadScope</key><string>System</string><key>PayloadContent</key><array><dict><key>PayloadDisplayName</key><string>Custom Settings</string><key>PayloadIdentifier</key><string>A8D9441D-17D9-47C8-AFC7-94DAE25C5E35</string><key>PayloadOrganization</key><string>JAMF Software</string><key>PayloadType</key><string>com.apple.ManagedClient.preferences</string><key>PayloadUUID</key><string>A8D9441D-17D9-47C8-AFC7-94DAE25C5E35</string><key>PayloadVersion</key><integer>1</integer><key>PayloadContent</key><dict><key>io.chippewa.gustave</key><dict><key>Forced</key><array><dict><key>mcx_preference_settings</key><dict><key>Secret</key><string>'$5'</string></dict></dict></array></dict></dict></dict></array></dict></plist>' | sed 's/</\&lt;/g' | sed 's/>/\&gt;/g')

# XML for the configuration profile
configProfileXML="<os_x_configuration_profile>
    <general>
        <name>$4</name>
        <description>Test Profile</description>
        <site>
            <id>-1</id>
            <name>None</name>
        </site>
         <category>
           <id>$6</id>
         </category>
        <distribution_method>Install Automatically</distribution_method>
        <user_removable>false</user_removable>
        <level>computer</level>
        <redeploy_on_update>Newly Assigned</redeploy_on_update>
        <payloads>$payloadXML</payloads>
    </general>
  <scope>
      <computers>
        <computer>
          <id>$7</id>
        </computer>
      </computers>
    </scope>
</os_x_configuration_profile>"

#echo "$configProfileXML"

# Create the configuration profile with payload
ProfileID=$(curl -sku "$jamfProUser":"$jamfProPass" "$jamfProURL/$apiEndPoint" -X POST -H "Content-Type: text/xml" -d "$configProfileXML")
echo $ProfileID
