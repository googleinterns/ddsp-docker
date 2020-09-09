var PROJECT_ID;
var CLIENT_ID;
var API_KEY;
var SCOPES;
var API_VERSION;

var DEFAULT_PROJECT;
var DEFAULT_REGION;
var DEFAULT_ZONE;
var DEFAULT_NAME;
var GOOGLE_PROJECT;
var DEFAULT_DISK_NAME;
var DEFAULT_IMAGE_FAMILY;
var BASE_URL;
var PROJECT_URL;
var GOOGLE_PROJECT_URL;
var DEFAULT_DISK_URL;
var DEFAULT_IMAGE_URL;
var DEFAULT_MACHINE_TYPE;
var DEFAULT_MACHINE_URL;
var DEFAULT_NETWORK;
var DEFAULT_SUBNETWORK;

function initializeApi() {
    gapi.client.load('compute', API_VERSION);
}

function authorization() {
    gapi.client.setApiKey(API_KEY);
    gapi.auth.authorize({
        client_id: CLIENT_ID,
        scope: SCOPES,
        immediate: false
    }, function (authResult) {
        if (authResult && !authResult.error) {
            initializeApi();
            switchComponents('vm_control', 'login');
        } else {
            window.alert('Auth was not successful');
        }
    }
    );
}

function switchComponents(idToShow, idToHide) {
    document.getElementById(idToShow).style.display = 'block';
    document.getElementById(idToHide).style.display = 'none';
}


function logIn() {
    PROJECT_ID = document.getElementById("project_id").value;
    CLIENT_ID = document.getElementById("client_id").value;
    API_KEY = document.getElementById("api_key").value;

    SCOPES = 'https://www.googleapis.com/auth/compute';
    API_VERSION = 'v1';

    DEFAULT_REGION = 'europe-west4';
    DEFAULT_ZONE = DEFAULT_REGION + '-a';
    DEFAULT_PROJECT = PROJECT_ID;
    DEFAULT_NAME = 'ddsp-docker';
    GOOGLE_PROJECT = 'debian-cloud';
    DEFAULT_DISK_NAME = DEFAULT_NAME;
    DEFAULT_IMAGE_FAMILY = 'debian-9';
    BASE_URL = 'https://www.googleapis.com/compute/' + API_VERSION;
    PROJECT_URL = BASE_URL + '/projects/' + DEFAULT_PROJECT;
    GOOGLE_PROJECT_URL = BASE_URL + '/projects/' + GOOGLE_PROJECT;
    DEFAULT_DISK_URL = PROJECT_URL + '/zones/' + DEFAULT_ZONE +
        '/disks/' + DEFAULT_DISK_NAME;
    DEFAULT_IMAGE_URL = GOOGLE_PROJECT_URL + '/global/images/family/' +
        DEFAULT_IMAGE_FAMILY;
    DEFAULT_MACHINE_TYPE = 'e2-medium';
    DEFAULT_MACHINE_URL = PROJECT_URL + '/zones/' + DEFAULT_ZONE +
        '/machineTypes/' + DEFAULT_MACHINE_TYPE;
    DEFAULT_NETWORK = PROJECT_URL + '/global/networks/default';
    DEFAULT_SUBNETWORK = PROJECT_URL + '/regions/' + DEFAULT_REGION +
        '/subnetworks/default';

    authorization();
}

function insertDisk() {
    var request = gapi.client.compute.disks.insert({
        'project': DEFAULT_PROJECT,
        'zone': DEFAULT_ZONE,
        'sourceImage': DEFAULT_IMAGE_URL,
        'resource': {
            'name': DEFAULT_DISK_NAME,
            'sizeGb': '40'
        }
    });
    request.execute(function (resp) {
        // Code to handle response
    });
}

function insertInstance() {
    resource = {
        'name': DEFAULT_NAME,
        'machineType': DEFAULT_MACHINE_URL,
        'networkInterfaces': [
            {
                'network': DEFAULT_NETWORK,
                'subnetwork': DEFAULT_SUBNETWORK,
                'accessConfigs': [
                    {
                        'type': 'ONE_TO_ONE_NAT',
                        'networkTier': 'PREMIUM'
                    }
                ],
            }
        ],
        'disks': [{
            'source': DEFAULT_DISK_URL,
            'type': 'PERSISTENT',
            'boot': true
        }],
        'metadata': {
            'items': [
                {
                    'key': 'startup-script',
                    'value': '#! /bin/bash\n\
                        curl -sSO https://dl.google.com/cloudagents/install-logging-agent.sh\n\
                        sudo bash install-logging-agent.sh\n\
                        apt update\n\
                        apt -y install unzip\n\
                        wget https://github.com///googleinterns/ddsp-docker/archive/web-interface.zip\n\
                        unzip web-interface.zip\n\
                        mv ddsp-docker-web-interface /opt/app\n\
                        cd /opt/app\n\
                        source setup.sh'
                }
            ],
        },
        'serviceAccounts': [
            {
                'scopes': [
                    'https://www.googleapis.com/auth/cloud-platform'
                ]
            }
        ],
        'tags': {
            'items': [
                'http-server'
            ]
        }
    };
    var request = gapi.client.compute.instances.insert({
        'project': DEFAULT_PROJECT,
        'zone': DEFAULT_ZONE,
        'resource': resource
    });
    request.execute(function (resp) {
        // Code to handle response
    });
}

function setUpVM() {
    insertDisk();
    setTimeout(insertInstance, 5000);
}

function executeRequest(request, trialCounter = 4, successFunction, failureFunction) {
    request.execute(function (resp) {
        if (resp.error && trialCounter > 0) {
            setTimeout(() => { executeRequest(request, trialCounter - 1, successFunction, failureFunction) }, 5000);
        }
        else if (resp.error) {
            failureFunction();
        }
        else {
            successFunction(resp);
        }
    });
}

function getInstance() {
    var request = gapi.client.compute.instances.get({
        'project': DEFAULT_PROJECT,
        'zone': DEFAULT_ZONE,
        'instance': DEFAULT_NAME
    });
    executeRequest(
        request,
        4,
        function(resp){
            vmAddress = resp.result['networkInterfaces'][0]['accessConfigs'][0]['natIP'];
            window.open('http://' + vmAddress + ':8080', '_blank');
        },
        () => {
            window.alert('Couldn\'t access VM :(\nTry setting it up once more!');
        });
}

function deleteInstance() {
    var request = gapi.client.compute.instances.delete({
        'project': DEFAULT_PROJECT,
        'zone': DEFAULT_ZONE,
        'instance': DEFAULT_NAME
    });
    request.execute(function (resp) {
        // Code to handle response
    });
}

function deleteDisk() {
    var request = gapi.client.compute.disks.delete({
        'project': DEFAULT_PROJECT,
        'zone': DEFAULT_ZONE,
        'disk': DEFAULT_DISK_NAME
    });
    executeRequest(
        request,
        4,
        function(resp){
            window.alert('Successfully cleaned up environment');
        },
        () => {
            window.alert('There was a problem while cleaning up :(\nTry once more!');
        });
}

function cleanUp() {
    deleteInstance();
    setTimeout(deleteDisk, 10000);
}