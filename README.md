# OctoPrint-MattaConnect
OctoPrint Plugin for internal development and data collection

## 🧐 About

This plugin is an internal data acquisition plugin for 3D printing, built to enable the development of learning 3D printers.

## 🔧 Plugin Development

OctoPlug-Internal is a standard OctoPrint plugin, more informatin about the development of such plugins can be found in the Developing Plugins webpage on the OctoPrint website: [http://docs.octoprint.org/en/master/plugins/](http://docs.octoprint.org/en/master/plugins/) or [getting started](https://docs.octoprint.org/en/master/plugins/gettingstarted.html) page. Please update the instructions below if outdated with later versions of OctoPrint.

First clone the repository, set up a virtual environment, and activate it.
```
git clone git@github.com:Matta-Labs/octoplug-internal.git
cd octoplug-internal
virtualenv -p python3 env
source env/bin/activate
```

If you do not have `virtualenv` installed, try installing it for your user account using:

```
pip3 install -U virtualenv
```

If this does not properly install `virtualenv` and you suffer from *command not found* errors search for how to install on your operating system.

It is recommended to install OctoPrint from source rather than the Python package repository, `pip` if you wish to modify the OctoPrint source and features, for example enabling acknowledgements and reponses from the virtual printer like in [Marlin](http://marlinfw.org/) the 3D printer firmware. Clone OctoPrint as presented below. If modifications to OctoPrint are not required, install as normal for plugin development with `pip3 install octoprint[develop, plugins]`.

If modifications to the OctoPrint source are required do the following:

```
git clone https://github.com/foosel/OctoPrint.git
cd OctoPrint
virtualenv env
source env/bin/activate
pip install --upgrade pip
pip install -e .[develop,plugins]
```

On M1 Macs there may be issues with the verison of `watchdog` being incompatible with the `arm` architecture reporting a *legacy-install-failure*. You made need to add some additional headers to your path to fix this problem.

Additionally install cookiecutter:
```
pip install "cookiecutter>=1.4,<1.7"
```

Install the plugin being developed with:
```
octoprint dev plugin:install
```

And run the octoprint server using:
```
octoprint serve
```

## 🚀 Plugin Installation on Pi

This plugin is not available from the OctoPrint Plugin Repository and as such must be installed manually - this however is very easy to do.

At first, you need to access the Raspberry Pi connected to the 3D printer which is running OctoPrint. This best way to do this is via `ssh`, e.g.

```shell
ssh pi@octopi.local
```

*Note: the default password for Pi's is `raspberry` it should probably be changed if it is still the password.*

Once on the Pi this git repo can be cloned and subsequently installed. To install the plugin in the correct location, the virtual environment used for OctoPrint must be activated. If you have installed OctoPrint via OctoPi (the Raspbian based SD card image for the Raspberry Pi that already includes OctoPrint plus everything you need to run it) then this is located at `~/oprint/bin/activate`. If you did a custom installed of OctoPrint you probably know where your virtual environment is.

```shell
git clone git@github.com:Matta-Labs/octoplug-internal.git
source ~/oprint/bin/activate
```

Now we have the correct environment we can easily install the packge using `pip` and subsequently reboot in order to load our plugin.

```shell
pip install -e octoplug-internal
sudo reboot
```

Thats it! Now the OctoPlug-Internal plugin should be installed.

## 🎈 Usage and Configuration

In settings there are a few variables which need to be configure for use:

- Server Address (this is the URL of the data collection server flask application)
- Camera Snapshot URLs
- Camera Intervals (seconds)
- Bed remover (toggle on or off)
- Mechanical tester (can specify target coordinates)

For data to be collected need to toggle with custom g-code commands `EXTRUDING_START` and `EXTRUDING_STOP`. Either manually enter these in the OctoPrint terminal or just add them to the slicer pre- and post-scripts. The reason for these is to not gather 100s of data points for more "boring" things such as heating up.
