# Written by phyllip2004
# This app functions as a middle man between a developer and CUCM. Uses flask to provide an API gateway to CUCM which is easier to read and understand.
# Think of this as a translator which can take standard API posts and will translate to SOAP then forward the request along returning the result.
# The purpose of this app is to simplify the method with which individuals query CUCM APIs as well as provide access control.
# v0.0.1

import flask
import requests
from flask import request
from xml.dom.minidom import parseString

app = flask.Flask(__name__)
app.config["DEBUG"] = True

url = "https://cucm-pub.huettfamily.com:8443/axl/"

@app.route('/', methods=['GET'])
def home():
    return '''<h1>Provisioning API</h1>
    <p>Do a dance.</p>'''

@app.route('/api/v1/macd/listphone', methods=['POST'])
def api_listphone():
    if 'name' in request.args:
        name = str(request.args['name'])
        searchCriteria = '<name>' + name + '</name>'
    if 'description' in request.args:
        description = str(request.args['description'])
        searchCriteria = '<description>' + description + '</description>'
    if 'protocol' in request.args:
        protocol = str(request.args['protocol'])
        searchCriteria = '<protocol>' + protocol + '</protocol>'
    if 'callingSearchSpaceName' in request.args:
        callingSearchSpaceName = str(request.args['callingSearchSpaceName'])
        searchCriteria = '<callingSearchSpaceName>' + callingSearchSpaceName + '</callingSearchSpaceName>'
    if 'devicePoolName' in request.args:
        devicePoolName = str(request.args['devicePoolName'])
        searchCriteria = '<devicePoolName>' + devicePoolName + '</devicePoolName>'
    if 'securityProfileName' in request.args:
        securityProfileName = str(request.args['securityProfileName'])
        searchCriteria = '<securityProfileName>' + securityProfileName + '</securityProfileName>'
        
    payload=f"<soapenv:Envelope xmlns:soapenv=\"http://schemas.xmlsoap.org/soap/envelope/\" xmlns:ns=\"http://www.cisco.com/AXL/API/12.5\"><soapenv:Header/><soapenv:Body><ns:listPhone><searchCriteria>{searchCriteria}</searchCriteria><returnedTags><name/><description/><ownerUserName/><protocol/><callingSearchSpaceName/><devicePoolName/><securityProfileName/></returnedTags></ns:listPhone></soapenv:Body></soapenv:Envelope>"
    headers = {
		'Authorization': 'Basic YXBwYWRtaW46cWF6d3N4UUFaV1NY',
		'Content-Type': 'text/plain',
		'Cookie': 'JSESSIONID=DC16695C6048F2C28E5C057ED6F9E7AB; JSESSIONIDSSO=23A9E493636E69AEA20CEBD3DDDBBB5E'
    }
    response = requests.request("POST", url, headers=headers, data=payload, verify=False)
    return str(response.content)

app.run()