# coding=utf-8
import flask
import base64
import octoprint.plugin
import signal
from .utils import init_sentry

from .matta import MattaCore
from .printer import MattaPrinter


class MattaconnectPlugin(
    octoprint.plugin.StartupPlugin,
    octoprint.plugin.ShutdownPlugin,
    octoprint.plugin.SettingsPlugin,
    octoprint.plugin.TemplatePlugin,
    octoprint.plugin.AssetPlugin,
    octoprint.plugin.SimpleApiPlugin,
    octoprint.plugin.EventHandlerPlugin,
):
    def get_settings_defaults(self):
        """Returns the plugin's default and configured settings"""
        return {
            "auth_token": "",
            "snapshot_url": "",
            "default_z_offset": "0.0",
            "nozzle_tip_coords_x": "10",
            "nozzle_tip_coords_y": "10",
            "snapshot_url": "http://localhost/webcam/?action=snapshot",
            "webrtc_url": "http://localhost/webcam/webrtc",
            "live_upload": False,
            "flip_h": False,
            "flip_v": False,
            "rotate": False,
        }

    def get_template_configs(self):
        """Returns the template configurations for the plugin"""
        self._logger.debug("MattaConnect - is loading template configurations. Okay.")
        return [dict(type="settings", custom_bindings=True)]

    def get_assets(self):
        """Returns the plugin's asset files to automatically include in the core UI"""
        return {
            "js": ["js/mattaconnect.js"],
            "css": ["css/mattaconnect.css"],
            "less": ["less/mattaconnect.less"],
        }

    def get_update_information(self):
        # Define the configuration for your plugin to use with the Software Update
        # Plugin here. See https://docs.octoprint.org/en/master/bundledplugins/softwareupdate.html
        # for details.
        return {
            "mattaconnect": {
                "displayName": "Mattaconnect Plugin",
                "displayVersion": self._plugin_version,
                # version check: github repository
                "type": "github_release",
                "user": "Matta-Labs",
                "repo": "octoprint-mattaconnect",
                "current": self._plugin_version,
                # update method: pip
                "pip": "https://github.com/Matta-Labs/octoprint-mattaconnect/archive/{target_version}.zip",
            }
        }

    def on_after_startup(self):
        """
        Function that runs after OctoPrint starts and the plugin is loaded.
        Sets up the threads and variables needed.
        """
        self._logger.debug("MattaConnect plugin - is starting up.")

    def initialize(self):
        """Initialize the plugin"""
        init_sentry(self._plugin_version)
        self.matta_os = MattaCore(self)

    def get_api_commands(self):
        """
        Returns the available API commands as a dictionary.

        Returns:
            dict: A dictionary of available API commands.
        """
        return dict(
            test_auth_token=["auth_token"],
            snapshot=["url"],
            set_enabled=[],
        )

    def is_api_adminonly(self):
        """
        Checks if API operations require administrative privileges.

        Returns:
            bool: True if administrative privileges are required, False otherwise.
        """
        return True

    def on_api_command(self, command, data):
        """
        Handles API commands received from the client.

        Args:
            command (str): The API command to be executed.
            data (dict): Additional data associated with the command.

        Returns:
            flask.Response: A JSON response containing the result of the command execution.
        """
        if command == "test_auth_token":
            auth_token = data["auth_token"]
            success, status_text = self.matta_os.test_auth_token(token=auth_token)
            return flask.jsonify({"success": success, "text": status_text})

        if command == "snapshot":
            success, status_text, image = self.matta_os.take_snapshot(url=data["url"])
            if image is not None:
                # Convert the image to base64
                image_base64 = base64.b64encode(image).decode("utf-8")
            else:
                image_base64 = None
            return flask.jsonify(
                {"success": success, "text": status_text, "image": image_base64}
            )

    def parse_received_lines(self, comm_instance, line, *args, **kwargs):
        """
        Parse received lines from the printer's communication and update the printer's state accordingly.

        Args:
            comm_instance: Communication instance.
            line (str): The received line from the printer.
            *args: Variable length argument list.
            **kwargs: Arbitrary keyword arguments.

        Returns:
            str: The parsed line.
        """
        try:
            self.matta_os._printer.parse_line_for_updates(line)
        except AttributeError:
            self.matta_os._printer = MattaPrinter(
                self._printer, self._logger, self._file_manager
            )

        if "UPDATED" in line:
            self.executed_update = True
            self.new_cmd = False
        return line

    def parse_sent_lines(
        self,
        comm_instance,
        phase,
        cmd,
        cmd_type,
        gcode,
        subcode=None,
        tags=None,
        *args,
        **kwargs,
    ):
        """
        Parse sent lines and update relevant attributes based on the sent commands.

        This method is called when a line is sent to the printer. It extracts information
        from the line and updates the corresponding attributes.

        Args:
            comm_instance: Communication instance.
            phase (str): The phase of the command.
            cmd (str): The command sent to the printer.
            cmd_type (str): The type of command.
            gcode (str): The G-code associated with the command.
            subcode (str): Subcode associated with the command (optional).
            tags (dict): Tags associated with the command (optional).
            *args: Variable length argument list.
            **kwargs: Arbitrary keyword arguments.

        Returns:
            str: The parsed command.
        """
        try:
            if tags:
                # tags is set in format: {'source:file', 'filepos:371', 'fileline:7'}
                if "source:file" in tags:
                    # get the current gcode line number
                    # find item starting with fileline
                    line = [
                        set_item for set_item in tags if set_item.startswith("fileline")
                    ][0]
                    # strip file line to get number
                    line = line.replace("fileline:", "")
                    self.matta_os._printer.gcode_line_num_no_comments = line
                    self.matta_os._printer.gcode_cmd = cmd
                elif "plugin:mattaconnect" in tags or "api:printer.command" in tags:
                    self.matta_os.terminal_cmds.append(cmd)
        except Exception as e:
            self._logger.error(e)
        return cmd


__plugin_name__ = "MattaConnect"
__plugin_pythoncompat__ = ">=3,<4"  # Only Python 3


def __plugin_load__():
    global __plugin_implementation__
    __plugin_implementation__ = MattaconnectPlugin()

    global __plugin_hooks__
    __plugin_hooks__ = {
        "octoprint.plugin.softwareupdate.check_config": __plugin_implementation__.get_update_information,
        "octoprint.comm.protocol.gcode.received": __plugin_implementation__.parse_received_lines,
        "octoprint.comm.protocol.gcode.sent": __plugin_implementation__.parse_sent_lines,
    }
