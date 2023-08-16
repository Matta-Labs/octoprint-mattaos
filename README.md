<p align="center"><img src="https://uploads-ssl.webflow.com/63fa465ee0545971ce735482/64883f3b58342c1b87033b6d_Emblem_Black.svg" alt="Matta Logo" style="width:90px" /></p>
<h1 align="center" style="margin-bottom:20px"><a href="https://matta.ai">MattaConnect</a></h1>

<p align="center">Connect your OctoPrint-connected printers to <a href="https://os.matta.ai">MattaOS</a>, for remote control, AI-powered error detection, fleet management, and more!</p>

## 🧐 About

The plugin allows users to control their printers using our intuitive web-interface, <a href="https://os.matta.ai">MattaOS</a>. MattaConnect brings Matta's data engine to OctoPrint, managing printer and webcam data, enabling next-level AI error detection and print job inspection.

<br/>
Matta is working towards building full AI-powered closed-loop control of 3D printing, enabling perfect quality, every time. By being an early user of our software, you help us build towards this goal!

## ✨ Features

- 🛜 Remote printer control via MattaOS, our intuitive web-interface.
- ⚡️ Advanced error detection using Matta's cutting-edge AI.
- 📈 Keep track of your printing operations with Printer Analytics.
- 👀 G-code viewer and analysis.
- ⚙️ Coming soon: Controllable failure behaviour (notify, pause, stop).

## 🚀 Plugin Installation
    
This plugin is not yet available from the OctoPrint Plugin Repository and as such must be installed manually - this however is very easy to do. 
<br/>
Below are a number of methods for installation:

<details>
  <summary><b>Install from ZIP in OctoPrint UI</b></summary>
    <br/>

Download the ZIP package for this repositiory using the green 'Code' dropdown above or the following code.

```shell
wget https://github.com/Matta-Labs/octoprint-mattaconnect/archive/refs/heads/main.zip
```

In OctoPrint's plugin manager, select "+ Get More", and upload the downloaded .zip file in the provided box.

Click "Install", and restart OctoPrint when prompted.

✨ Thats it! Now the MattaConnect plugin should be installed.

</details>
<details>
  <summary><b>Clone onto Pi via SSH</b></summary>
    <br/>

At first, you need to access the Raspberry Pi connected to the 3D printer which is running OctoPrint. This best way to do this is via `ssh`, e.g.

```shell
ssh pi@octopi.local
```

*Note: the default password for Pi's is `raspberry` it should probably be changed if it is still the password.*

Once on the Pi this git repo can be cloned and subsequently installed. To install the plugin in the correct location, the virtual environment used for OctoPrint must be activated. If you have installed OctoPrint via OctoPi (the Raspbian based SD card image for the Raspberry Pi that already includes OctoPrint plus everything you need to run it) then this is located at `~/oprint/bin/activate`. If you did a custom installed of OctoPrint you probably know where your virtual environment is.

```shell
git clone git@github.com:Matta-Labs/octoprint-mattaconnect.git
source ~/oprint/bin/activate
```

Now we have the correct environment we can easily install the packge using `pip` and subsequently reboot in order to load our plugin.

```shell
pip install -e octoprint-mattaconnect
sudo reboot
```

✨ Thats it! Now the MattaConnect plugin should be installed.
</details>


## 🎈 Usage and Configuration

First sign-up for a free Matta account at <a>https://os.matta.ai</a>, then configure plugin settings to get started!

In settings there are a few variables which need to be configured for use:

<details>
<summary><b>Authorisation token </b>(from MattaOS)</summary>

1. Create a printer in MattaOS.
2. Copy the Authorisation token from the new printer's setup page.
3. Paste this into the Authorisation token box in MattaConnect settings.
4. Click "Authorise" to connect the printer to MattaOS!
</details>
<br/>
<details>
<summary><b>WebRTC Stream URL*</b></summary>

<br/>

This is the streaming URL of your nozzle-cam streamer. The plugin only supports WebRTC streams, which require OctoPrint 1.8.0 and above.

<br/>

</details>
<details>
<summary><b>Camera Snapshot URL*</b></summary>
<br/>

This is the snapshot URL of your nozzle-cam streamer. The plugin only supports WebRTC streams, which require OctoPrint 1.8.0 and above.

1. Paste in the streamer snapshot URL.
2. Click snap to test the connection.
3. On the retreved snapshot, click the nozzle tip to show Grey where to look!
</details>
<br/>
<p>*required for AI-powered error detection</p>

## More About Matta 🔷

<div  align="center" >
  <img src="https://matta-os.fra1.cdn.digitaloceanspaces.com/site-assets/matta-about.png" alt="Matta info">
</div>
<br/>
At <a href="https://matta.ai"><strong>Matta</strong></a>, we are building AI to push the boundaries of manufacturing. We train neural networks using vision to become manufacturing copilots, enabling next-generation error correction, material qualitification and part QC.

<br/>

<a href="https://matta.ai/greymatta"><strong>Check out the demo of our first-iteration AI, Grey-1</strong></a>



## Contact 📞

Team Matta - [@mattaai](https://twitter.com/mattaai) - hello@matta.ai

Project Link: [https://github.com/Matta-Labs/octoprint-mattaconnect](https://github.com/Matta-Labs/octoprint-mattaconnect)

<p align="right">(<a href="#readme-top">back to top</a>)</p>
