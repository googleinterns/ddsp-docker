# DDSP-Docker 🐳 web interface 

## Train a DDSP Autoencoder on Google Cloud AI Platform with just a few clicks.
This guide will walk you through creating a project on Google Cloud Platform, getting the right credentials, and using [DDSP Docker web interface](https://googleinterns.github.io/ddsp-docker/) to train a DDSP Autoencoder on Google Cloud AI Platform.

In the end, you'll have a custom-trained checkpoint that you can download to use with the [DDSP Timbre Transfer Colab](https://colab.research.google.com/github/magenta/ddsp/blob/master/ddsp/colab/demos/timbre_transfer.ipynb).
![](https://storage.googleapis.com/ddsp/additive_diagram/ddsp_autoencoder.png)

## Quickstart
There are a few steps you need to complete before using the [DDSP Docker web interface](https://googleinterns.github.io/ddsp-docker/).

### Activate [Google Cloud Platform's Free Trial](https://cloud.google.com/free)
If you are a new GCP user you will get $300 to spend on it. That's more than enough to train DDSP Autoencoder.
### Create a [GCP project](https://console.cloud.google.com/projectcreate)
![](https://raw.githubusercontent.com/googleinterns/ddsp-docker/web-interface/documentation_images/new_project.png)
### Get right credentials
1. Go to [APIs & Services](https://console.cloud.google.com/apis) in the GCP Console.
2. In the left-most panel click on [OAuth consent screen](https://console.cloud.google.com/apis/credentials/consent).
3. Choose **External** User Type and click **CREATE**.
![](https://raw.githubusercontent.com/googleinterns/ddsp-docker/web-interface/documentation_images/consent_screen.png)
4. Type in the **Application name** and click **SAVE**.
![](https://raw.githubusercontent.com/googleinterns/ddsp-docker/web-interface/documentation_images/consent_screen_name.png)
5. In the left-most panel click [Credentials](https://console.cloud.google.com/apis/credentials).
6. Click **+ CREATE CREDENTIALS** and choose the **API key**.
![](https://raw.githubusercontent.com/googleinterns/ddsp-docker/web-interface/documentation_images/api_key.png)
7. Click **+ CREATE CREDENTIALS** and choose the **OAuth client ID**.
![](https://raw.githubusercontent.com/googleinterns/ddsp-docker/web-interface/documentation_images/client_id.png)
8. Set **Application type** to the **Web application**.
![](https://raw.githubusercontent.com/googleinterns/ddsp-docker/web-interface/documentation_images/application_type.png)
9. Add URI in the **Authorised JavaScript origins**. Type in https://googleinterns.github.io and click **CREATE**.
![](https://raw.githubusercontent.com/googleinterns/ddsp-docker/web-interface/documentation_images/javascript_origins.png)

### Log in through our web interface
1. Go to https://googleinterns.github.io/ddsp-docker.
2. Type in your **Project ID**, copy the **API key**, and **Client ID** you've just created, and click log in.

![](https://raw.githubusercontent.com/googleinterns/ddsp-docker/web-interface/documentation_images/login.png)

## Web Interface
Here you will find some tips on the pipeline of using the [DDSP Docker web interface](https://googleinterns.github.io/ddsp-docker/).

### Set up a Google Compute Engine VM
1. **Activate GCE API** by clicking the link on the webpage and following the next instructions.
2. Click the **Create VM** button.
3. Click the **Go to VM** button. As creating a VM takes a while, you may need to wait a little bit before accessing it.

![](https://raw.githubusercontent.com/googleinterns/ddsp-docker/web-interface/documentation_images/setup_vm.png)

### Preprocess your audio data
1. Upload .mp3 or .wav files. It should be 10-20 minutes of audio from a single monophonic source (also, one acoustic environment).
2. Click the **Preprocess button**. Preprocessing the data should take around 10-15 minutes. Note that you may need to wait here for a while as some setup processes may still be running in the background and they need to be completed before submitting the preprocessing job.

![](https://raw.githubusercontent.com/googleinterns/ddsp-docker/web-interface/documentation_images/file_upload.png)

### Run training job on AI Platform
1. Choose the training parameters.
2. Click the **Submit** button.
3. Check training job status by clicking the **Check training job status** button.
4. Observe the training process using TensorBoard. Refresh TensorBoard by clicking the **Upload new logs to TensorBoard** button and following a **Observe your experiment on TensorBoard** link.

![](https://raw.githubusercontent.com/googleinterns/ddsp-docker/web-interface/documentation_images/tensorboard.png)
![](https://raw.githubusercontent.com/googleinterns/ddsp-docker/web-interface/documentation_images/tensorboard_graphs.png)

#### Training notes:
* Models typically perform well when the loss drops to the range of ~4.5-5.0.
* Depending on the dataset, chosen batch size, and learning rate this can take anywhere from 5k-40k training steps usually.
* There are [two special configurations](https://github.com/googleinterns/ddsp-docker/tree/master/magenta_docker#note-on-cluster-configuration-and-hyperparameters) prepared, one time and one prize optimized. A proper configuration file will be used based on your batch size choice. Note: your project may not have enough quota to use the speed optimized configuration (you will be notified if that is the case).

### Download the trained model
1. Click the **Download model** button.
2. You are now ready to use [DDSP Timbre Transfer Colab](https://colab.research.google.com/github/magenta/ddsp/blob/master/ddsp/colab/demos/timbre_transfer.ipynb).

![](https://raw.githubusercontent.com/googleinterns/ddsp-docker/web-interface/documentation_images/model_downloaded.png)

### Clean up the environment
1. Click the **Delete bucket** button.
2. Return to the [login webpage](https://googleinterns.github.io/ddsp-docker), login once more if necessary, and click the **Clean up** button.

![](https://raw.githubusercontent.com/googleinterns/ddsp-docker/web-interface/documentation_images/clean_up.png)
