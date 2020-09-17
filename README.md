# DDSP-Docker Web Interface 

## Train a DDSP Autoencoder on Google Cloud AI Platform with just a few clicks.
This guide will walk you through creating a project on Google Cloud Platform, getting right credentials and using our [web interface](https://googleinterns.github.io/ddsp-docker/) to train a DDSP Autoencoder on Google Cloud AI Platform.

At the end, you'll have a custom-trained checkpoint that you can download to use with the [DDSP Timbre Transfer Colab](https://colab.research.google.com/github/magenta/ddsp/blob/master/ddsp/colab/demos/timbre_transfer.ipynb).
![](https://storage.googleapis.com/ddsp/additive_diagram/ddsp_autoencoder.png)

## Quickstart
There are a few steps you need to complete before using our Web Interface.

### Activate [Google Cloud Platform's Free Trial](https://cloud.google.com/free)
If you are a new GCP user you will get $300 to spent on it. That's more than enough to train DDSP Autoencoder.
### Create [GCP project](https://console.cloud.google.com/projectcreate)
### Get right credentials
1. Go to [APIs & Services](https://console.cloud.google.com/apis) in the GCP Console.
2. In the left-most panel click on [OAuth consent screen](https://console.cloud.google.com/apis/credentials/consent).
3. Choose External User Type and click CREATE.
4. Type in Application name and click Save.
5. In the left-most panel click [Credentials](https://console.cloud.google.com/apis/credentials).
6. Click CREATE CREDENTIALS and choose API key.
7. Click CREATE CREDENTIALS and choose OAuth client ID.
8. Set Application type to Web application.
9. Add URI in the Authorised JavaScript origins. Type in https://googleinterns.github.io and click CREATE.

### Log in through our web interface
1. Go to https://googleinterns.github.io/ddsp-docker
2. Type in your Project ID, copy API key and Client ID you've just created and click log in.

## Web Interface
Here you will find some tips on the pipeline of using the Web Interface.

### Set up a Google Compute Engine VM
1. Activate GCE API.
2. Click Create VM.
3. Click Go to VM. As creating a VM takes a while, you may need to wait a little bit before accessing it.

### Preprocess your audio data
1. Upload .mp3 or .wav files. It should be 10-20 minutes of audio from a single monophonic source (also, one acoustic environment).
2. Click Preprocess button. Preprocessing the data should take around 10-15 minutes. Note that you may need to wait here for a while as some setup processes are still ran in the background and they need to be completed before submitting the preprocessing job.



