var PROJECT_ID;
var CLIENT_ID;
var API_KEY;
var SCOPES = 'https://www.googleapis.com/auth/compute';
var API_VERSION = 'v1';

var DEFAULT_PROJECT = PROJECT_ID;
var DEFAULT_ZONE = 'europe-west4-a';

/**
 * Load the Google Compute Engine API.
 */
function initializeApi() {
    gapi.client.load('compute', API_VERSION);
}

/**
 * Authorize Google Compute Engine API.
 */
function authorization() {
    gapi.client.setApiKey(API_KEY);
    gapi.auth.authorize({
        client_id: CLIENT_ID,
        scope: SCOPES,
        immediate: false
    }, function (authResult) {
        if (authResult && !authResult.error) {
            window.alert('Auth was successful!');
            initializeApi();
        } else {
            window.alert('Auth was not successful');
        }
    }
    );
}

var DEFAULT_NAME = 'test-node';
var GOOGLE_PROJECT = 'debian-cloud'; // project hosting a shared image
var DEFAULT_DISK_NAME = DEFAULT_NAME;
var DEFAULT_IMAGE_FAMILY = 'debian-9';

var BASE_URL = 'https://www.googleapis.com/compute/' + API_VERSION;
var PROJECT_URL = BASE_URL + '/projects/' + DEFAULT_PROJECT;
var GOOGLE_PROJECT_URL = BASE_URL + '/projects/' + GOOGLE_PROJECT;
var DEFAULT_DISK_URL = PROJECT_URL + '/zones/' + DEFAULT_ZONE +
    '/disks/' + DEFAULT_DISK_NAME;
var DEFAULT_IMAGE_URL = GOOGLE_PROJECT_URL + '/global/images/family/' +
    DEFAULT_IMAGE_FAMILY;

var DEFAULT_IMAGE_NAME = DEFAULT_NAME;
var DEFAULT_MACHINE_TYPE = 'n1-standard-1';

var DEFAULT_MACHINE_URL = PROJECT_URL + '/zones/' + DEFAULT_ZONE +
    '/machineTypes/' + DEFAULT_MACHINE_TYPE;
var DEFAULT_NETWORK = PROJECT_URL + '/global/networks/default';

/**
     * Google Compute Engine API request to insert a disk into your cluster.
     */
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

/**
* Google Compute Engine API request to insert your instance
*/
function insertInstance() {
    resource = {
        "name": DEFAULT_NAME,
        "machineType": "https://www.googleapis.com/compute/v1/projects/werror-2020/zones/"+DEFAULT_ZONE+"/machineTypes/e2-medium",
        "zone": "https://www.googleapis.com/compute/v1/projects/werror-2020/zones/"+DEFAULT_ZONE,
        "canIpForward": false,
        "networkInterfaces": [
            {
                "network": "https://www.googleapis.com/compute/v1/projects/werror-2020/global/networks/default",
                "subnetwork": "https://www.googleapis.com/compute/v1/projects/werror-2020/regions/europe-west4/subnetworks/default",
                "name": "nic0",
                "accessConfigs": [
                    {
                        "type": "ONE_TO_ONE_NAT",
                        "name": "External NAT",
                        "networkTier": "PREMIUM",
                        "kind": "compute#accessConfig"
                    }
                ],
                "kind": "compute#networkInterface"
            }
        ],
        'disks': [{
            'source': DEFAULT_DISK_URL,
            'type': 'PERSISTENT',
            'boot': true
        }],
        "metadata": {
            "items": [
                {
                    "key": "startup-script",
                    "value": "#! /bin/bash\napt update\napt -y install unzip\nwget https://github.com//werkaaa/magenta_gce_vm/archive/master.zip\nunzip master.zip\ncd magenta_gce_vm-master\nsource setup.sh"
                }
            ],
            "kind": "compute#metadata"
        },
        "serviceAccounts": [
            {
                "scopes": [
                    "https://www.googleapis.com/auth/cloud-platform"
                ]
            }
        ],
        "selfLink": "https://www.googleapis.com/compute/v1/projects/werror-2020/zones/"+DEFAULT_ZONE+"/instances/instance-test",
        "scheduling": {
            "onHostMaintenance": "MIGRATE",
            "automaticRestart": true,
            "preemptible": false
        },
        "cpuPlatform": "Intel Haswell",
        "startRestricted": false,
        "deletionProtection": false,
        "reservationAffinity": {
            "consumeReservationType": "ANY_RESERVATION"
        },
        "displayDevice": {
            "enableDisplay": false
        },
        "kind": "compute#instance"
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

function setupVM() {
    PROJECT_ID = document.getElementById("project_id").value;
    CLIENT_ID = document.getElementById("client_id").value;
    API_KEY = document.getElementById("api_key").value;
    authorization(PROJECT_ID, CLIENT_ID, API_KEY);
    setTimeout(insertDisk, 5000);
    setTimeout(insertInstance, 5000);
}
