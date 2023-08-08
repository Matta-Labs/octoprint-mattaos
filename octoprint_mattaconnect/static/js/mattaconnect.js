/*
 * View model for OctoPrint-Octoplug-internal
 *
 * Author: Douglas Brion | Matta Labs Ltd
 * License: AGPLv3
 */
$(function() {

    var settings_test_btn = document.getElementById("settings_test_btn");
    settings_test_btn.onclick = function() {
        var settings_test_btn_spin = document.getElementById("settings_test_btn_spin");
        settings_test_btn_spin.style.display = "inline-block";
        settings_test_token();
    };

    var navbar_test_btn = document.getElementById("navbar_test_btn");
    navbar_test_btn.onclick = function() {
        var navbar_test_btn_spin = document.getElementById("navbar_test_btn_spin");
        navbar_test_btn_spin.style.display = "inline-block";
        settings_test_token();
    };

    settings_test_token = function() {
        console.log(document.getElementById("settings_token_input").value);
        var data = {
            command: "test_auth_token",
            auth_token: document.getElementById("settings_token_input").value,
        };
        $.ajax({
            // url for /api/plugin/matta_os getting base and port from window.location
            url: window.location.origin + "/api/plugin/matta_os",
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


    
    function MattaconnectViewModel(parameters) {

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

        const flip_h_box = document.getElementById("flip_h");
        const flip_v_box = document.getElementById("flip_v");
        const rotation_box = document.getElementById("rotate");
        const rotation_container = document.getElementById("camPreviewContainer");
        const rotation_image = document.getElementById("camPreview");
        const camPreviewContainer = document.getElementById('camPreviewContainer');
        const settings_snap_btn = document.getElementById("settings_snap_btn");

        settings_snap_btn.addEventListener('click', function(event){
            snap_image();
        });
        

        function snap_image(){

            let camPreview = document.getElementById("camPreview");
            let snapshotUrlInput = document.getElementById("settings_snap_input").value;
            camPreview.src = snapshotUrlInput + new Date().getTime();
            camPreview.onload = function(){
                updateImageTransform();
            }
            console.log(camPreview.src);
            console.log("snap image");
        };


        function updateImageDimensions() {

            let naturalWidth = camPreview.naturalWidth;
            let naturalHeight = camPreview.naturalHeight;

            let aspectRatio = naturalHeight / naturalWidth;

            let width = 400;
            let height = width * aspectRatio;

            if (self.rotate()) {
                rotation_container.style.width = height + "px";
                rotation_container.style.height = width + "px";
                rotation_image.style.width = width + "px";
                rotation_image.style.maxWidth = width + "px";
                rotation_image.style.height = height + "px";
                rotation_image.style.maxHeight = height + "px";

            } else {
                rotation_container.style.width = width + "px";
                rotation_container.style.height = height + "px";
                rotation_image.style.width = width + "px";
                rotation_image.style.maxWidth = width + "px";
                rotation_image.style.height = height + "px";
                rotation_image.style.maxHeight = height + "px";

            }
            console.log("The natural width is "+naturalWidth );
            console.log("The natural height is "+naturalHeight );
            console.log("Successfully changed CSS params");
            console.log("The aspect ratio is "+aspectRatio);
        }


        camPreviewContainer.addEventListener('click', function (event) {
            let rect = camPreviewContainer.getBoundingClientRect();
            let x = event.clientX - rect.left;
            let y = event.clientY - rect.top;
            updateCrosshairPosition(x, y);
        });

        function updateCrosshairPosition(x, y) {
            const crosshair = document.querySelector(".crosshair");
            crosshair.style.left = x + 'px';
            crosshair.style.top = y + 'px';
            document.getElementById("crosshair").style.display = "block";
            calculateAndUpdateNozzleCoords(x, y);
        }
    
        function calculateAndUpdateNozzleCoords(x, y) {
            let myImage = document.getElementById("camPreview");
    
            let naturalWidth = myImage.naturalWidth;
            let naturalHeight = myImage.naturalHeight;
    
            let clientWidth = myImage.clientWidth;
            let clientHeight = myImage.clientHeight;
            
            const nozzle_tip_coords_x = document.getElementById("nozzle_tip_coords_x");
            const nozzle_tip_coords_y = document.getElementById("nozzle_tip_coords_y");
            nozzle_tip_coords_x.textContent = parseInt(x / clientWidth * naturalWidth);
            nozzle_tip_coords_y.textContent = parseInt(y / clientHeight * naturalHeight);

            self.nozzle_tip_coords_x(parseInt(x / clientWidth * naturalWidth));
            self.nozzle_tip_coords_y(parseInt(y / clientHeight * naturalHeight)); 
        }

        flip_h_box.addEventListener('change', function (event) {
            updateImageTransform();
            document.getElementById("crosshair").style.display = "none";
        });
    
        flip_v_box.addEventListener('change', function (event) {
            updateImageTransform();
            document.getElementById("crosshair").style.display = "none";
        });
    
        rotation_box.addEventListener('change', function (event) {
            updateImageTransform();
            document.getElementById("crosshair").style.display = "none";
        });

        function rotateContainer(){
            rotation_container.classList.remove("camPreviewContainerNoRotate");
            rotation_container.classList.add("camPreviewContainerRotate");
        }
        function rotateImage(){
            rotation_image.classList.remove("imgNoRotate");
            rotation_image.classList.add("imgRotate");
        }
        function resetContainer(){
            rotation_container.classList.remove("camPreviewContainerRotate");
            rotation_container.classList.add("camPreviewContainerNoRotate");
        }
        function resetImage(){
            rotation_image.classList.remove("imgRotate");
            rotation_image.classList.add("imgNoRotate");
        }

        function updateImageTransform() {

            updateImageDimensions();
            console.log("update image transform")

            if (self.rotate() == false) {
                resetContainer();
                resetImage();
            } else {
                rotateContainer();
                rotateImage();
            }

            if (self.flip_h() == true && self.flip_v() == true && self.rotate() == false){ 
                rotation_image.style.transformOrigin = '50% 50%';
                rotation_image.style.transform = 'scale(-1,-1)';
            }
            else if (self.flip_h() == true && self.flip_v() == false && self.rotate() == false){ 
                rotation_image.style.transformOrigin = 'top left';
                rotation_image.style.transform = 'scaleX(-1) translate(-100%)';
            }
            else if (self.flip_h() == false && self.flip_v() == true && self.rotate() == false){
                rotation_image.style.transformOrigin = '50% 50%';
                rotation_image.style.transform = 'scaleY(-1)';
            }
            else if (self.flip_h() == false && self.flip_v() == false && self.rotate() == false){
                rotation_image.style.transform = 'rotate(0deg)'
            }
            else if (self.flip_h() == false && self.flip_v() == false && self.rotate() == true){
                rotation_image.style.transformOrigin = 'top left';
                rotation_image.style.transform = 'rotate(270deg) translate(-100%)';
            }
            else if (self.flip_h() == true && self.flip_v() == false && self.rotate() == true){
                rotation_image.style.transformOrigin = 'top left';
                rotation_image.style.transform = 'scaleX(-1) rotate(90deg)';
            }
            else if (self.flip_h() == false && self.flip_v() == true && self.rotate() == true){
                rotation_image.style.transformOrigin = 'top left';
                rotation_image.style.transform = 'scaleY(-1) rotate(90deg) translate(-100%,-100%)';
            } 
            else {
                rotation_image.style.transformOrigin = 'top left';
                rotation_image.style.transform = 'scale(-1,-1) rotate(270deg) translate(0%,-100%)';
            }
        }
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
