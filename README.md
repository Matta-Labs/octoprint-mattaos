<p align="center"><img src="https://uploads-ssl.webflow.com/63fa465ee0545971ce735482/64883f3b58342c1b87033b6d_Emblem_Black.svg" alt="Matta Logo" style="width:50px" /></p>
<h1 align="center" style="margin-bottom:20px"><a href="https://matta.ai">MattaOS</a> for OctoPrint</h1>
<img src="https://matta-os.fra1.cdn.digitaloceanspaces.com/site-assets/email_assets/VideoGridCover.png" />
<p>Connect your OctoPrint-connected printers to <a href="https://os.matta.ai">MattaOS</a>, for remote control, AI-powered error detection, fleet management, and more!</p>

## 🧐 About

The plugin allows users to control their printers using our intuitive web-interface, <a href="https://os.matta.ai">Matta OS</a>. Matta OS brings Matta's data engine to OctoPrint, managing printer and webcam data, enabling next-level AI error detection and print job inspection. All that is required is a simple nozzle camera, and an OctoPrint-running 3D printer.

Matta is working towards building full AI-powered closed-loop control of 3D printing, enabling perfect quality, every time. By being an early user of our software, you help us build towards this goal!
## ✨ Features

- 🛜 Remote printer control via MattaOS, our intuitive web-interface.
- ⚡️ Advanced error detection using Matta's cutting-edge AI.
- 📈 Keep track of your printing operations with Printer Analytics.
- 👀 G-code viewer and analysis.
- ⚙️ Controllable failure behaviour (notify, pause, stop).

<br/>
<div align="center"><img src="https://matta-os.fra1.cdn.digitaloceanspaces.com/site-assets/MattaOS.gif" width=650 /><p>Monitoring a print with MattaOS</p></div>
<br/>



## 🐙 OctoPrint Camera Stack Installation

OctoPrint-MattaOS is a plugin for <a href="https://github.com/OctoPrint/OctoPrint">OctoPrint</a>, the snappy web interface for your 3D printer. If you have not setup OctoPrint, get started <a href="https://octoprint.org" > here.</a>

The Matta OS OctoPrint plugin uses the <a href="https://octoprint.org/blog/2023/05/24/a-new-camera-stack-for-octopi">new camera stack for OctoPi</a>. If you have not already got the new camera stack, you must flash your Pi and install the new OctoPi image.

<br/>
<div align="center"><img src="https://matta-os.fra1.cdn.digitaloceanspaces.com/site-assets/octopisetup.gif" width=500 /><p>Installing OctoPi with new camera stack using Raspberry Pi Imager</p></div>
<br/>



## 🚀 Plugin Installation
    
This plugin is not yet available from the OctoPrint Plugin Repository and as such must be installed manually - this however is very easy to do. 

<br/>

Below are a number of methods for installation:
<details>
  <summary><b>From URL in the OctoPrint UI</b></summary>
    <br/>

Copy the following URL to the latest version of Matta OS's OctoPrint plugin:

```shell
https://github.com/Matta-Labs/octoprint-mattaos/archive/refs/heads/main.zip
```

In OctoPrint's plugin manager, select "+ Get More", and paste this URL into the "...From URL" section in the OctoPrint plugin manager inside the input with "Enter URL..".

Click "Install", and restart OctoPrint when prompted.

</details>
<details>
  <summary><b>From an uploaded ZIP file in the OctoPrint UI</b></summary>
    <br/>

Download the ZIP package for this repositiory using the green 'Code' dropdown above or the following code.

```shell
wget https://github.com/Matta-Labs/octoprint-mattaos/archive/refs/heads/main.zip
```

In OctoPrint's plugin manager, select "+ Get More", and upload the downloaded .zip file in the provided box.

Click "Install", and restart OctoPrint when prompted.

✨ Thats it! Now the MattaOS plugin should be installed.

(Note: We have noticed an issue with installing on Mac if Safari is used to download the ZIP package. Please ensure Safari preferences are set such that downloaded files are not automatically opened upon download).

</details>
<details>
  <summary><b>Clone onto Pi via SSH</b></summary>
    <br/>

At first, you need to access the Raspberry Pi connected to the 3D printer which is running OctoPrint. This best way to do this is via `ssh`, e.g.

```shell
ssh pi@octopi.local
```

*Note: the default password for Pi's is `raspberry` it should probably be changed if it is still the password.*

Once on the Pi this git repo can be cloned and subsequently installed. To install the plugin in the correct location, the virtual environment used for OctoPrint must be activated. If you have installed OctoPrint via OctoPi (the Raspbian based SD card image for the Raspberry Pi that already includes OctoPrint plus everything you need to run it) then this is located at `~/oprint/bin/activate`. If you did a custom install of OctoPrint you probably know where your virtual environment is.

```shell
git clone git@github.com:Matta-Labs/octoprint-mattaos.git
source ~/oprint/bin/activate
```

Now we have the correct environment we can easily install the packge using `pip` and subsequently reboot in order to load our plugin.

```shell
pip install -e octoprint-mattaos
sudo reboot
```

✨ Thats it! Now the MattaOS plugin should be installed.
</details>


<br/>

OctoPrint sets the default image capture format to YUYV, however better streaming results can acheived with MJPEG. This can be changed in the `/boot/usb-default.conf` file on your Raspberry Pi as follows:
<br/>

```shell 
sudo nano /boot/camera-streamer/usb-default.conf
```

Set the format to MJPEG:


```shell
# The image format of the camera.
FORMAT=MJPEG
```
Save and close the file and reboot the Pi.
<br/>



## 📸 Nozzle Cameras

If you don't already have a nozzle camera installed, check our our <a href="https://github.com/Matta-Labs/camera-mounts">camera-mounts repository</a> to aid installation.

Also please feel free to contribute your own nozzle camera designs to the repo!
<br/>



## 🎈 Usage and Configuration

First sign-up for a free Matta account at <a>https://os.matta.ai</a>, then configure plugin settings to get started!

Create a new machine in MattaOS, copy the generated Authorisation token, then head to the MattaOS plugin settings in OctoPrint to configure the plugin.

<br/>
<div align="center"><img src="https://matta-os.fra1.cdn.digitaloceanspaces.com/site-assets/MattaOSSetupCrop.gif" width=650 /><p>Machine setup and plugin configuration workflow</p></div>
<br/>

In settings there are a few variables which need to be configured for use:

<details>
<summary><b>Authorisation token </b>(from MattaOS)</summary>

1. Create a printer in MattaOS.
2. Copy the Authorisation token from the new printer's setup page.
3. Paste this into the Authorisation token box in MattaOS settings.
4. Click "Authorise" to connect the printer to MattaOS!
</details>

<details>
<summary><b>WebRTC Stream URL*</b></summary>

<br/>

This is the streaming URL of your nozzle-cam streamer. The plugin only supports WebRTC streams, which require OctoPrint 1.8.0 and above, with the new camera stack.

This will be ```http://<the hostname (or IP) of your Raspberry Pi>/webcam/webrtc```. Replace localhost with the hostname (or IP).

<br/>

</details>
<details>
<summary><b>Camera Snapshot URL*</b></summary>
<br/>

This is the snapshot URL of your nozzle-cam streamer. The plugin only supports WebRTC streams, which require OctoPrint 1.8.0 and above, with the new camera stack.

This will be ```http://<the hostname (or IP) of your Raspberry Pi>/webcam/?action=snapshot```

1. Paste in the streamer snapshot URL.
2. Click snap to test the connection.
3. On the retreived snapshot, click the nozzle tip to show Grey where to look!
</details>
<br/>
<p>*required for AI-powered error detection</p>

The new OctoPi camera stack provides a useful control interface for the camera device. Once set up, you can find this at ```https://<the hostname (or IP) of your Raspberry Pi>/webcam/control```. Use this to focus your camera on the printer nozzle so that Grey-1 can accurately find errors.

<br/>
<div align="center"><img src="https://matta-os.fra1.cdn.digitaloceanspaces.com/site-assets/CameraStreamerControl.png" width=650 ><p>Camera-streamer control web interface</p></div>
<br/>



## 🔷 More About Matta

<div  align="center" >
  <img src="https://matta-os.fra1.cdn.digitaloceanspaces.com/site-assets/matta-about.png" alt="Matta info">
</div>
<br/>
At <a href="https://matta.ai"><strong>Matta</strong></a>, we are building AI to push the boundaries of manufacturing. We train neural networks using vision to become manufacturing copilots, enabling next-generation error correction, material qualitification and part QC.

<br/>
<br/>

<a href="https://matta.ai/greymatta"><strong>Check out the demo of our first-iteration AI, Grey-1</strong></a>


<br/>

## 📞 Contact 

Team Matta - [@mattalabs](https://twitter.com/mattalabs) - hello@matta.ai

Project Link: [https://github.com/Matta-Labs/octoprint-mattaos](https://github.com/Matta-Labs/octoprint-mattaos)

<p align="right">(<a href="#readme-top">back to top</a>)</p>
