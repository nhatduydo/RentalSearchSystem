window.onload = function () {
    console.log("togglePassword.js loaded!");

    document.addEventListener("DOMContentLoaded", function () {
        var passwordInput = document.getElementById("password");

        if (passwordInput) {
            var wrapper = document.createElement("div");
            wrapper.style.position = "relative";
            wrapper.style.display = "inline-block";

            var toggleButton = document.createElement("button");
            toggleButton.type = "button";
            toggleButton.textContent = "👁️";
            toggleButton.style.position = "absolute";
            toggleButton.style.right = "5px";
            toggleButton.style.top = "50%";
            toggleButton.style.transform = "translateY(-50%)";
            toggleButton.style.border = "none";
            toggleButton.style.background = "none";
            toggleButton.style.cursor = "pointer";

            toggleButton.addEventListener("click", function () {
                if (passwordInput.type === "password") {
                    passwordInput.type = "text";
                    toggleButton.textContent = "🙈";
                } else {
                    passwordInput.type = "password";
                    toggleButton.textContent = "👁️";
                }
            });

            passwordInput.parentNode.insertBefore(wrapper, passwordInput);
            wrapper.appendChild(passwordInput);
            wrapper.appendChild(toggleButton);
        }
    });
};
