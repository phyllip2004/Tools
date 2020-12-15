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

@app.route('/api/v1/macd/list_phone', methods=['POST'])
def api_list_phone():
    if 'searchName' in request.args:
        searchName = str(request.args['searchName'])
        searchCriteria = '<name>' + searchName + '</name>'
    if 'searchDescription' in request.args:
        searchDescription = str(request.args['searchDescription'])
        searchCriteria = '<description>' + searchDescription + '</description>'
        
    payload=f"<soapenv:Envelope xmlns:soapenv=\"http://schemas.xmlsoap.org/soap/envelope/\" xmlns:ns=\"http://www.cisco.com/AXL/API/12.5\"><soapenv:Header/><soapenv:Body><ns:listPhone><searchCriteria>{searchCriteria}</searchCriteria><returnedTags><name/><description/><ownerUserName/></returnedTags></ns:listPhone></soapenv:Body></soapenv:Envelope>"
    headers = {
		'Authorization': 'Basic YXBwYWRtaW46cWF6d3N4UUFaV1NY',
		'Content-Type': 'text/plain',
		'Cookie': 'JSESSIONID=DC16695C6048F2C28E5C057ED6F9E7AB; JSESSIONIDSSO=23A9E493636E69AEA20CEBD3DDDBBB5E'
    }
    response = requests.request("POST", url, headers=headers, data=payload, verify=False)
    return str(response.content)
app.run()