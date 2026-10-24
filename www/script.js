// Ensure elements are visible when the page loads
document.addEventListener("DOMContentLoaded", function() {
    document.getElementById("textinput").style.display = "flex";
});

// Initialize Particle.js
particlesJS("particles-js", {
    "particles": {
        "number": { "value": 100, "density": { "enable": true, "value_area": 800 }},
        "color": { "value": "#00ffff" },
        "shape": { "type": "circle" },
        "opacity": { "value": 1 },
        "size": { "value": 3, "random": true },
        "line_linked": { "enable": true, "distance": 150, "color": "#00ffff", "opacity": 0.75, "width": 1 },
        "move": { "enable": true, "speed": 9, "direction": "none", "out_mode": "out" }
    },
    "interactivity": {
        "detect_on": "canvas",
        "events": { "onhover": { "enable": false }, "onclick": { "enable": false } }
    }
});

$(document).ready(function () {
    $('.text').textillate({

        loop:true,
        sync:true,
        in:{
            effect:"bounceIn"
        },
        out:{
            effect:"bounceOut"
        }

    })
   
});

document.addEventListener("DOMContentLoaded", function () {
    // Prevent multiple SiriWave instances
    if (window.siriWaveInstance) {
        console.log("SiriWave already initialized.");
        return;
    }

    // Initialize SiriWave and store in a global variable
    window.siriWaveInstance = new SiriWave({
        container: document.getElementById("siri-container"),
        width: 600,
        height: 200,
        style: "ios9",
        amplitude: 2,
        speed: 0.1,
        autostart: true,
        color: "#ffffff"
    });

    // Adjust wave when mic is clicked
    const micBtn = document.getElementById("MicBtn");
    micBtn.addEventListener("click", function () {
        window.siriWaveInstance.setSpeed(0.2);
        window.siriWaveInstance.setAmplitude(2);
    });

    console.log("SiriWave initialized successfully.");
});

$(document).ready(function () {
    $('.siri-message').textillate({
        loop: true,  // Keeps animating in a loop
        sync: true,  // Animates all letters at the same time
        in: {
            effect: "fadeInUp",  // Animation when text appears
            sync :true,// Controls speed of effect
        },
        out: {
            effect: "fadeOutUp",  // Animation when text appears
            sync :true,
        }
    });

$("#MicBtn").click(function (e) { 
    try {
        if (typeof eel.playAssistantSound === "function") {
            eel.playAssistantSound();
        }
    } catch (err) {
        console.log("Sound error:", err);
    }
   
    $("#Oval").attr("hidden",true);
    $("#SiriWave").attr("hidden",false);
    eel.allCommands();
});

});

$(document).ready(function () {
    function PlayAssistant(message) {

        if (message != "") {

            $("#Oval").attr("hidden", true);
            $("#SiriWave").attr("hidden", false);
            eel.allCommands(message);
            $("#chatbox").val("")
            $("#MicBtn").attr('hidden', false);
            $("#SendBtn").attr('hidden', true);

        }

    }

    // toogle fucntion to hide and display mic and send button 
    function ShowHideButton(message) {
        if (message.length == 0) {
            $("#MicBtn").attr('hidden', false);
            $("#SendBtn").attr('hidden', true);
        }
        else {
            $("#MicBtn").attr('hidden', true);
            $("#SendBtn").attr('hidden', false);
        }
    }

    // key up event handler on text box
    $("#chatbox").keyup(function () {

        let message = $("#chatbox").val();
        ShowHideButton(message)
    
    });
    
    // send button event handler
    $("#SendBtn").click(function () {
    
        let message = $("#chatbox").val()
        PlayAssistant(message)
    
    });

    $("#chatbox").keypress(function (e) {
        key = e.which;
        if (key == 13) {
            let message = $("#chatbox").val()
            PlayAssistant(message)
        }
    });
});

$("#homeBtn").click(function (e) { 
    eel.playAssistantSound()
   
    $("#Oval").attr("hidden",false);
    $("#SiriWave").attr("hidden",true);
    
});

