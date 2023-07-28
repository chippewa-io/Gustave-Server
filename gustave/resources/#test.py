#test.py
import requests
import xml.etree.ElementTree as ET

#Set Variables:
jamfProURL = "https://tcohoon.jamfcloud.com"
jamfProUser = "admin"
jamfProPass = "jamf1234"
profile_name = "badtest"
secret = "junksecret"
expiration = "1690591053"
category_id = "33"
computer_id = "173"

def create_payload_xml(profile_name, secret, expiration):
    root = ET.Element("plist", version="1.0")

    dict_elem = ET.SubElement(root, "dict")
    ET.SubElement(dict_elem, "key").text = "PayloadUUID"
    ET.SubElement(dict_elem, "string").text = "42884445-1B56-4EA4-A3D6-7009702F5CC7"
    ET.SubElement(dict_elem, "key").text = "PayloadType"
    ET.SubElement(dict_elem, "string").text = "Configuration"
    ET.SubElement(dict_elem, "key").text = "PayloadOrganization"
    ET.SubElement(dict_elem, "string").text = "Jamf"
    ET.SubElement(dict_elem, "key").text = "PayloadIdentifier"
    ET.SubElement(dict_elem, "string").text = "42884445-1B56-4EA4-A3D6-7009702F5CC7"
    ET.SubElement(dict_elem, "key").text = "PayloadDisplayName"
    ET.SubElement(dict_elem, "string").text = profile_name
    ET.SubElement(dict_elem, "key").text = "PayloadDescription"
    ET.SubElement(dict_elem, "string").text = ""
    ET.SubElement(dict_elem, "key").text = "PayloadVersion"
    ET.SubElement(dict_elem, "integer").text = "1"
    ET.SubElement(dict_elem, "key").text = "PayloadEnabled"
    ET.SubElement(dict_elem, "true")
    ET.SubElement(dict_elem, "key").text = "PayloadRemovalDisallowed"
    ET.SubElement(dict_elem, "true")
    ET.SubElement(dict_elem, "key").text = "PayloadScope"
    ET.SubElement(dict_elem, "string").text = "System"
    ET.SubElement(dict_elem, "key").text = "PayloadContent"
    array_elem = ET.SubElement(dict_elem, "array")
    dict2_elem = ET.SubElement(array_elem, "dict")
    ET.SubElement(dict2_elem, "key").text = "PayloadDisplayName"
    ET.SubElement(dict2_elem, "string").text = "Custom Settings"
    ET.SubElement(dict2_elem, "key").text = "PayloadIdentifier"
    ET.SubElement(dict2_elem, "string").text = "D9A57B93-83DE-40C5-AF59-B3E17B76041A"
    ET.SubElement(dict2_elem, "key").text = "PayloadOrganization"
    ET.SubElement(dict2_elem, "string").text = "JAMF Software"
    ET.SubElement(dict2_elem, "key").text = "PayloadType"
    ET.SubElement(dict2_elem, "string").text = "com.apple.ManagedClient.preferences"
    ET.SubElement(dict2_elem, "key").text = "PayloadUUID"
    ET.SubElement(dict2_elem, "string").text = "D9A57B93-83DE-40C5-AF59-B3E17B76041A"
    ET.SubElement(dict2_elem, "key").text = "PayloadVersion"
    ET.SubElement(dict2_elem, "integer").text = "1"
    ET.SubElement(dict2_elem, "key").text = "PayloadContent"
    dict3_elem = ET.SubElement(dict2_elem, "dict")
    ET.SubElement(dict3_elem, "key").text = "io.chippewa.gustave"
    dict4_elem = ET.SubElement(dict3_elem, "dict")
    ET.SubElement(dict4_elem, "key").text = "Forced"
    array2_elem = ET.SubElement(dict4_elem, "array")
    dict5_elem = ET.SubElement(array2_elem, "dict")
    ET.SubElement(dict5_elem, "key").text = "mcx_preference_settings"
    dict6_elem = ET.SubElement(dict5_elem, "dict")
    ET.SubElement(dict6_elem, "key").text = "Secret"
    dict7_elem = ET.SubElement(dict6_elem, "dict")
    ET.SubElement(dict7_elem, "key").text = "Expiration"
    ET.SubElement(dict7_elem, "integer").text = str(expiration)
    ET.SubElement(dict7_elem, "key").text = "value"
    ET.SubElement(dict7_elem, "string").text = secret

    # Convert the XML structure to a string
    xml_string = ET.tostring(root).decode()
    
    # Escape the XML string
    xml_string = xml_string.replace("<", "&lt;").replace(">", "&gt;")
    
    return xml_string


def create_configuration_profile(jamfProURL, jamfProUser, jamfProPass, profile_name, secret, expiration, category_id, computer_id):
    # Create the XML payload for the profile
    payloadXML = create_payload_xml(profile_name, secret, expiration)

    # Now, construct the larger XML structure for the configuration profile
    configProfileXML = f"""
    <os_x_configuration_profile>
        <general>
            <name>{profile_name}</name>
            <description>Test Profile</description>
            <site>
                <id>-1</id>
                <name>None</name>
            </site>
             <category>
               <id>{category_id}</id>
             </category>
            <distribution_method>Install Automatically</distribution_method>
            <user_removable>true</user_removable>
            <level>computer</level>
            <redeploy_on_update>Newly Assigned</redeploy_on_update>
            <payloads>{payloadXML}</payloads>
        </general>
      <scope>
          <computers>
            <computer>
              <id>{computer_id}</id>
            </computer>
          </computers>
        </scope>
    </os_x_configuration_profile>
    """

    # Make the API call to Jamf Pro
    apiEndPoint = "JSSResource/osxconfigurationprofiles/id/0"
    headers = {"Content-Type": "text/xml"}
    auth = (jamfProUser, jamfProPass)
    
    response = requests.post(f"{jamfProURL}/{apiEndPoint}", data=configProfileXML, headers=headers, auth=auth)
    
    # Return the profile ID from the response
    return response.text
create_configuration_profile(jamfProURL, jamfProUser, jamfProPass, profile_name, secret, expiration, category_id, computer_id)