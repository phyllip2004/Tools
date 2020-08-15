"""
Version 0.1.0
Written by phyllip2004
Take a csv and create an XML for use in MTPutty
"""

import csv
import xml.etree.ElementTree as ET
from xml.dom import minidom


def prettify(elem):
    rough_string = ET.tostring(elem, 'utf-8')
    parsed = minidom.parseString(rough_string)
    return parsed.toprettyxml(indent="  ")


with open('DeviceList.csv') as csv_file:
    # configure csv reader
    csv_reader = csv.reader(csv_file, delimiter=',')

    # build xml
    root = ET.Element('Servers')
    putty = ET.SubElement(root, 'Putty')
    topNode = ET.SubElement(putty, 'Node')
    topNode.set('Type', '0')
    topNode.set('Expanded', '1')
    topDisplayName = ET.SubElement(topNode, 'DisplayName')
    topDisplayName.text = 'Voice Gateways'

    # build each device
    line_count = 0
    for row in csv_reader:
        if line_count == 0:
            line_count += 1
        else:
            node = ET.SubElement(topNode, 'Node')
            node.set('Type', '1')
            serverName = ET.SubElement(node, 'ServerName')
            serverName.text = str(row[1])
            displayName = ET.SubElement(node, 'DisplayName')
            displayName.text = str(row[0] + ' (' + str(row[1]) + ')')
            userName = ET.SubElement(node, 'UserName')
            userName.text = str(row[2])
            password = ET.SubElement(node, 'Password')
            password.text = str(row[3])
            clParams = ET.SubElement(node, 'CLParams')
            if len(row[2]) > 0:
                if len(row[3]) > 0:
                    clParams.text = str(row[1]) + ' -ssh -l ' + str(row[2]) + ' -pw *****'
                else:
                    clParams.text = str(row[1]) + ' -ssh -l ' + str(row[2])
            else:
                clParams.text = str(row[1]) + ' -ssh'
            line_count += 1

    output_file = open('import_this.xml', 'w')
    output_file.write(prettify(root))
    output_file.close()
