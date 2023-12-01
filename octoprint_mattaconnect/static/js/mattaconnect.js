/*
 * View model for OctoPrint-MattaConnect
 *
 * Author: Douglas Brion | Matta Labs Ltd
 * License: AGPLv3
 */
$(function() {
    
    function MattaconnectViewModel(parameters) {

        //---------------------------------------------------
        // Knockout observables, and page load functions
        //---------------------------------------------------

        var self = this;

        self.loginState = parameters[0];
        self.settings = parameters[1];
        
        self.auth_token = ko.observable();
        self.snapshot_url = ko.observable();
        self.webrtc_url = ko.observable();
        self.default_z_offset = ko.observable();
        self.nozzle_tip_coords_x = ko.observable();
        self.nozzle_tip_coords_y = ko.observable();
        self.flip_h = ko.observable();
        self.flip_v = ko.observable();
        self.rotate = ko.observable();
        
        self.auth_token.subscribe(function(new_auth_token) {
            self.settings.settings.plugins.mattaconnect.auth_token(new_auth_token);
        });
        self.snapshot_url.subscribe(function(new_snapshot_url) {
            self.settings.settings.plugins.mattaconnect.snapshot_url(new_snapshot_url);
        });
        self.webrtc_url.subscribe(function(new_webrtc_url) {
            self.settings.settings.plugins.mattaconnect.webrtc_url(new_webrtc_url);
        });
        self.default_z_offset.subscribe(function(new_offset) {
            self.settings.settings.plugins.mattaconnect.default_z_offset(new_offset);
        });
        self.nozzle_tip_coords_x.subscribe(function(new_nozzle_tip_coords_x) {
            self.settings.settings.plugins.mattaconnect.nozzle_tip_coords_x(new_nozzle_tip_coords_x);
        });
        self.nozzle_tip_coords_y.subscribe(function(new_nozzle_tip_coords_y) {
            self.settings.settings.plugins.mattaconnect.nozzle_tip_coords_y(new_nozzle_tip_coords_y);
        });
        self.flip_h.subscribe(function(new_flip_h) {
            self.settings.settings.plugins.mattaconnect.flip_h(new_flip_h);
        });
        self.flip_v.subscribe(function(new_flip_v) {
            self.settings.settings.plugins.mattaconnect.flip_v(new_flip_v);
        });
        self.rotate.subscribe(function(new_rotate) {
            self.settings.settings.plugins.mattaconnect.rotate(new_rotate);
        });

        self.onBeforeBinding = function() {
            self.auth_token(self.settings.settings.plugins.mattaconnect.auth_token());
            self.snapshot_url(self.settings.settings.plugins.mattaconnect.snapshot_url());
            self.webrtc_url(self.settings.settings.plugins.mattaconnect.webrtc_url());
            self.default_z_offset(self.settings.settings.plugins.mattaconnect.default_z_offset());
            self.nozzle_tip_coords_x(self.settings.settings.plugins.mattaconnect.nozzle_tip_coords_x());
            self.nozzle_tip_coords_y(self.settings.settings.plugins.mattaconnect.nozzle_tip_coords_y());
            self.flip_h(self.settings.settings.plugins.mattaconnect.flip_h());
            self.flip_v(self.settings.settings.plugins.mattaconnect.flip_v());
            self.rotate(self.settings.settings.plugins.mattaconnect.rotate());
        };

        self.onAfterBinding = function() {
            self.snap_image();
            self.updateCrosshairOnLoad();
        }

        self.updateCrosshairOnLoad = function() {
            camPreview.onload = function() {
                let scaleFactor = CAM_PREVIEW_WIDTH / camPreview.naturalWidth;
                crosshair.style.left = parseInt(self.nozzle_tip_coords_x() * scaleFactor) + "px";
                crosshair.style.top = parseInt(self.nozzle_tip_coords_y() * scaleFactor) + "px";
                self.updateImageTransform(); // TODO remove Hacky fix for transform on load bug;
                                             // TODO it should've done this in snap_image
            }
            nozzle_tip_coords_x.textContent = self.nozzle_tip_coords_x();
            nozzle_tip_coords_y.textContent = self.nozzle_tip_coords_y();
        }
        

        //---------------------------------------------------
        // Constants
        //---------------------------------------------------

        // TODO: Change the overall process to an easier flow process (so users can just do everything once linearly)
        // TODO: Help users with the webrtc_url and snapshot_url, by filling ip in it? Find out why 'localhost' is not working? (ip probs ez to get)
        // * idea: allow os.matta.ai to change nozzle_tip_coords_x, nozzle_tip_coords_y, and flips/rotate. 
        // * idea: Have nice CSS with matta logo picture on the plugin so it looks nice

        const CAM_PREVIEW_WIDTH = 400;
        const IMAGE_PLACEHOLDER = "https://matta-os.fra1.cdn.digitaloceanspaces.com/site-assets/placeholder.png"

        const settings_snap_btn = document.getElementById("settings_snap_btn");
        const camPreviewContainer = document.getElementById("camPreviewContainer");
        const camPreview = document.getElementById("camPreview");
        const crosshair = document.getElementById("crosshair");
        const nozzle_tip_coords_x = document.getElementById("nozzle_tip_coords_x");
        const nozzle_tip_coords_y = document.getElementById("nozzle_tip_coords_y");
        const flip_h_box = document.getElementById("flip_h");
        const flip_v_box = document.getElementById("flip_v");
        const rotation_box = document.getElementById("rotate");
        

        //---------------------------------------------------
        // Snap Image and transform options
        //---------------------------------------------------

        settings_snap_btn.addEventListener('click', function(event){
            self.snap_image();
        });
        
        self.snap_image = function() {
            let snapshotUrlInput = document.getElementById("settings_snap_input").value;
            camPreview.src = snapshotUrlInput + "?t=" + new Date().getTime();
            camPreview.onload = function() {
                if (camPreview.naturalWidth > 0 && camPreview.naturalHeight > 0) {
                    self.updateImageTransform();
                } else {
                    console.log("Snapshot not found.");
                    camPreview.src = IMAGE_PLACEHOLDER;
                }
            };
            camPreview.onerror = function() {
                console.log("Error loading snapshot.");
                camPreview.src = IMAGE_PLACEHOLDER;
            };
        };

        self.updateImageDimensions = function() {
            let aspectRatio = camPreview.naturalHeight / camPreview.naturalWidth;
            let width = CAM_PREVIEW_WIDTH;
            let height = width * aspectRatio;

            if (self.rotate()) {
                camPreviewContainer.style.width = height + "px";
                camPreviewContainer.style.height = width + "px";
                camPreview.style.width = width + "px";
                camPreview.style.maxWidth = width + "px";
                camPreview.style.height = height + "px";
                camPreview.style.maxHeight = height + "px";
            } else {
                camPreviewContainer.style.width = width + "px";
                camPreviewContainer.style.height = height + "px";
                camPreview.style.width = width + "px";
                camPreview.style.maxWidth = width + "px";
                camPreview.style.height = height + "px";
                camPreview.style.maxHeight = height + "px";
            }
        }

        flip_h_box.addEventListener('change', function (event) {
            self.updateImageTransform();
            crosshair.style.display = "none";
        });
    
        flip_v_box.addEventListener('change', function (event) {
            self.updateImageTransform();
            crosshair.style.display = "none";
        });
    
        rotation_box.addEventListener('change', function (event) {
            self.updateImageTransform();
            crosshair.style.display = "none";
        });

        self.updateImageTransform = function() {
            self.updateImageDimensions();

            if (!self.flip_h() && !self.flip_v() && !self.rotate()){
                camPreview.style.transform = 'none'
            } else if (self.flip_h() && !self.flip_v() && !self.rotate()){ 
                camPreview.style.transform = 'scaleX(-1) translate(-100%)';
            } else if (!self.flip_h() && self.flip_v() && !self.rotate()){
                camPreview.style.transform = 'scaleY(-1) translateY(-100%)';
            } else if (self.flip_h() && self.flip_v() && !self.rotate()){ 
                camPreview.style.transform = 'scale(-1,-1) translate(-100%,-100%)';
            } else if (!self.flip_h() && !self.flip_v() && self.rotate()){
                camPreview.style.transform = 'rotate(270deg) translate(-100%)';
            } else if (self.flip_h() && !self.flip_v() && self.rotate()){
                camPreview.style.transform = 'scaleX(-1) rotate(90deg)';
            } else if (!self.flip_h() && self.flip_v() && self.rotate()){
                camPreview.style.transform = 'scaleY(-1) rotate(90deg) translate(-100%,-100%)';
            } else if (self.flip_h() && self.flip_v() && self.rotate()){
                camPreview.style.transform = 'scale(-1,-1) rotate(270deg) translate(0%,-100%)';
            }
            console.log("Updated Image Transforms")
        }


        //---------------------------------------------------
        // Crosshair functions
        //---------------------------------------------------

        camPreviewContainer.addEventListener('click', function (event) {
            let rect = camPreviewContainer.getBoundingClientRect();
            let x = event.clientX - rect.left;
            let y = event.clientY - rect.top;
            self.updateCrosshairPosition(x, y);
        });

        self.updateCrosshairPosition = (x, y) => {
            crosshair.style.left = x + 'px';
            crosshair.style.top = y + 'px';
            crosshair.style.display = "block";
            self.calculateAndUpdateNozzleCoords(x, y);
        }
    
        self.calculateAndUpdateNozzleCoords = (x, y) => {
            let naturalWidth = camPreview.naturalWidth;
            let naturalHeight = camPreview.naturalHeight;
    
            let clientWidth = camPreview.clientWidth;
            let clientHeight = camPreview.clientHeight;
            
            nozzle_tip_coords_x.textContent = parseInt(x / clientWidth * naturalWidth);
            nozzle_tip_coords_y.textContent = parseInt(y / clientHeight * naturalHeight);

            self.nozzle_tip_coords_x(parseInt(x / clientWidth * naturalWidth));
            self.nozzle_tip_coords_y(parseInt(y / clientHeight * naturalHeight)); 
        }

        
        //---------------------------------------------------
        // Auth token functions
        //---------------------------------------------------

        const settings_test_btn = document.getElementById("settings_test_btn");
        const settings_test_btn_spin = document.getElementById("settings_test_btn_spin");
        const navbar_test_btn = document.getElementById("navbar_test_btn");
        const navbar_test_btn_spin = document.getElementById("navbar_test_btn_spin");
        const settings_token_input = document.getElementById("settings_token_input");

        settings_test_btn.onclick = function() {
            settings_test_btn_spin.style.display = "inline-block";
            self.settings_test_token();
        };
    
        navbar_test_btn.onclick = function() {
            navbar_test_btn_spin.style.display = "inline-block";
            self.settings_test_token();
        };
    
        self.settings_test_token = function() {
            console.log(`Connecting to Matta OS with token: ${settings_token_input.value}`)
            let data = {
                command: "test_auth_token",
                auth_token: settings_token_input.value,
            };
            $.ajax({
                // url for /api/plugin/matta_os getting base and port from window.location
                // /api/plugin/matta_os for working in octoplug-internal, /api/plugin/mattaconnect for working in MattaConnect
                url: window.location.origin + "/api/plugin/mattaconnect",
                type: "POST",
                data: JSON.stringify(data),
                contentType: "application/json",
                dataType: "json",
                success: function(status) {
                    if (status.success) {
                    new PNotify({
                        title: gettext("Connection"),
                        text: gettext(status.text),
                        type: "success"
                    });
                    } else {
                    new PNotify({
                        title: gettext("Connection"),
                        text: gettext(status.text),
                        type: "error"
                    });
                    }
                    settings_test_btn_spin.style.display = "none";
                    navbar_test_btn_spin.style.display = "none";
                }
            });
        };
    }
    

    /* view model class, parameters for constructor, container to bind to
     * Please see http://docs.octoprint.org/en/master/plugins/viewmodels.html#registering-custom-viewmodels for more details
     * and a full list of the available options.
     */
    OCTOPRINT_VIEWMODELS.push({
        construct: MattaconnectViewModel,
        dependencies: ["loginStateViewModel", "settingsViewModel"],
        elements: ["#settings_plugin_mattaconnect", "#navbar_plugin_mattaconnect"],
    });
});
