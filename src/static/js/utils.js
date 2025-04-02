// Copy functionality
function copyText(className) {
  let textToCopy;

  if (className === "directory-structure") {
    // For directory structure, get the hidden input value
    const hiddenInput = document.getElementById("directory-structure-content");
    if (!hiddenInput) return;
    textToCopy = hiddenInput.value;
  } else {
    // For other elements, get the textarea value
    const textarea = document.querySelector("." + className);
    if (!textarea) return;
    textToCopy = textarea.value;
  }

  const button = document.querySelector(
    `button[onclick="copyText('${className}')"]`
  );
  if (!button) return;

  // Copy text
  navigator.clipboard
    .writeText(textToCopy)
    .then(() => {
      // Store original content
      const originalContent = button.innerHTML;

      // Change button content
      button.innerHTML = "Copied!";

      // Reset after 1 second
      setTimeout(() => {
        button.innerHTML = originalContent;
      }, 1000);
    })
    .catch((err) => {
      // Show error in button
      const originalContent = button.innerHTML;
      button.innerHTML = "Failed to copy";
      setTimeout(() => {
        button.innerHTML = originalContent;
      }, 1000);
    });
}

function handleSubmit(event, showLoading = false) {
  event.preventDefault();
  const form = event.target || document.getElementById("ingestForm");
  if (!form) return;

  const submitButton = form.querySelector('button[type="submit"]');
  if (!submitButton) return;

  const formData = new FormData(form);

  // Update file size - check if we're using direct input or slider
  const slider = document.getElementById("file_size");
  const sizeValueInput = document.getElementById("size_value_input");

  if (slider && sizeValueInput) {
    // Check if we have an exact value stored in the data attribute
    if (sizeValueInput.dataset.exactValue) {
      // Use the exact value that was directly entered by the user
      formData.delete("max_file_size");
      formData.delete("exact_file_size");
      formData.append("max_file_size", slider.value); // Still send slider position for backward compatibility
      formData.append("exact_file_size", sizeValueInput.dataset.exactValue); // Send the exact value in KB
    } else {
      // Get the direct input value if it exists
      const directInputValue = sizeValueInput.value.trim();
      const numericMatch = directInputValue.match(
        /^(\d+(?:\.\d+)?)\s*(kb|mb|k|m|)$/i
      );

      if (numericMatch) {
        // If we have a valid direct input, use that value directly
        let value = parseFloat(numericMatch[1]);
        const unit = numericMatch[2].toLowerCase();

        // Convert to KB
        if (unit === "m" || unit === "mb") {
          value = value * 1024;
        }

        // Store the exact value in KB in a hidden field
        formData.delete("max_file_size");
        formData.delete("exact_file_size");
        formData.append("max_file_size", slider.value); // Still send slider position for backward compatibility
        formData.append("exact_file_size", value.toString()); // Send the exact value in KB
      } else {
        // If input is invalid, fall back to slider value
        formData.delete("max_file_size");
        formData.append("max_file_size", slider.value);
      }
    }
  }

  // Update pattern type and pattern
  const patternType = document.getElementById("pattern_type");
  const pattern = document.getElementById("pattern");
  if (patternType && pattern) {
    formData.delete("pattern_type");
    formData.delete("pattern");
    formData.append("pattern_type", patternType.value);
    formData.append("pattern", pattern.value);
  }

  const originalContent = submitButton.innerHTML;
  const currentStars = document.getElementById("github-stars")?.textContent;

  if (showLoading) {
    submitButton.disabled = true;
    submitButton.innerHTML = `
            <div class="flex items-center justify-center">
                <svg class="animate-spin h-5 w-5 text-gray-900" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                    <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
                    <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                </svg>
                <span class="ml-2">Processing...</span>
            </div>
        `;
    submitButton.classList.add("bg-[#ffb14d]");
  }

  // Submit the form
  fetch(form.action, {
    method: "POST",
    body: formData,
  })
    .then((response) => response.text())
    .then((html) => {
      // Store the star count before updating the DOM
      const starCount = currentStars;

      // Replace the entire body content with the new HTML
      document.body.innerHTML = html;

      // Wait for next tick to ensure DOM is updated
      setTimeout(() => {
        // Reinitialize slider functionality
        initializeSlider();

        const starsElement = document.getElementById("github-stars");
        if (starsElement && starCount) {
          starsElement.textContent = starCount;
        }

        // Scroll to results if they exist
        const resultsSection = document.querySelector("[data-results]");
        if (resultsSection) {
          resultsSection.scrollIntoView({ behavior: "smooth", block: "start" });
        }
      }, 0);
    })
    .catch((error) => {
      submitButton.disabled = false;
      submitButton.innerHTML = originalContent;
    });
}

function copyFullDigest() {
  const directoryStructure = document.getElementById(
    "directory-structure-content"
  ).value;
  const filesContent = document.querySelector(".result-text").value;
  const fullDigest = `${directoryStructure}\n\nFiles Content:\n\n${filesContent}`;
  const button = document.querySelector('[onclick="copyFullDigest()"]');
  const originalText = button.innerHTML;

  navigator.clipboard
    .writeText(fullDigest)
    .then(() => {
      button.innerHTML = `
            <svg class="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7"></path>
            </svg>
            Copied!
        `;

      setTimeout(() => {
        button.innerHTML = originalText;
      }, 2000);
    })
    .catch((err) => {
      console.error("Failed to copy text: ", err);
    });
}

// Add the logSliderToSize helper function
function logSliderToSize(position) {
  const minp = 0;
  const maxp = 500;
  const minv = Math.log(1);
  const maxv = Math.log(102400);

  const value = Math.exp(minv + (maxv - minv) * Math.pow(position / maxp, 1.5));
  return Math.round(value);
}

// Move slider initialization to a separate function
function initializeSlider() {
  const slider = document.getElementById("file_size");
  const sizeValueInput = document.getElementById("size_value_input");

  if (!slider || !sizeValueInput) return;

  function updateSliderFromInput() {
    // Parse the input value to extract the number and unit
    const inputValue = sizeValueInput.value.trim();
    const numericMatch = inputValue.match(/^(\d+(?:\.\d+)?)\s*(kb|mb|k|m|)$/i);

    if (!numericMatch) {
      // Reset to current slider value if invalid input
      updateSliderUI();
      return;
    }

    let value = parseFloat(numericMatch[1]);
    const unit = numericMatch[2].toLowerCase();

    // Convert to KB if necessary
    if (unit === "m" || unit === "mb") {
      value = value * 1024;
    }

    // Store the exact value as a data attribute for form submission
    sizeValueInput.dataset.exactValue = value.toString();

    // Find the slider position that corresponds to this KB value
    // Inverse of the logSliderToSize function
    const minv = Math.log(1);
    const maxv = Math.log(102400);
    const maxp = 500;

    // Solve for position: value = exp(minv + (maxv - minv) * (position/maxp)^1.5)
    // Taking log of both sides: log(value) = minv + (maxv - minv) * (position/maxp)^1.5
    // Rearranging: (log(value) - minv) / (maxv - minv) = (position/maxp)^1.5
    // Taking the 1/1.5 power of both sides: ((log(value) - minv) / (maxv - minv))^(1/1.5) = position/maxp
    // Solving for position: position = maxp * ((log(value) - minv) / (maxv - minv))^(1/1.5)

    const logValue = Math.log(value);
    const position =
      maxp * Math.pow((logValue - minv) / (maxv - minv), 1 / 1.5);

    // Update slider value
    slider.value = Math.min(Math.max(Math.round(position), 0), maxp);

    // Update slider background without changing the input value
    slider.style.backgroundSize = `${(slider.value / slider.max) * 100}% 100%`;
  }

  function updateSliderUI() {
    const value = logSliderToSize(slider.value);

    // Always update the exact value when slider changes
    sizeValueInput.dataset.exactValue = value.toString();

    // Format the size for display
    const formattedSize = formatSize(value);

    // Always update the input value when the slider changes
    sizeValueInput.value = formattedSize;

    // Update slider background
    slider.style.backgroundSize = `${(slider.value / slider.max) * 100}% 100%`;
  }

  // Update on slider change
  slider.addEventListener("input", function () {
    updateSliderUI();
  });

  // Update on input field change
  sizeValueInput.addEventListener("change", function () {
    // Parse the input value to extract the number and unit
    const inputValue = sizeValueInput.value.trim();
    const numericMatch = inputValue.match(/^(\d+(?:\.\d+)?)\s*(kb|mb|k|m|)$/i);

    if (numericMatch) {
      let value = parseFloat(numericMatch[1]);
      const unit = numericMatch[2].toLowerCase();

      // Convert to KB if necessary
      if (unit === "m" || unit === "mb") {
        value = value * 1024;
      }

      // Store the exact value for form submission
      sizeValueInput.dataset.exactValue = value.toString();
    }

    updateSliderFromInput();
  });
  sizeValueInput.addEventListener("blur", updateSliderFromInput);
  sizeValueInput.addEventListener("keydown", function (e) {
    if (e.key === "Enter") {
      updateSliderFromInput();
      e.preventDefault();
    }
  });

  // Initialize slider position
  updateSliderUI();
}

// Add helper function for formatting size
function formatSize(sizeInKB) {
  // For slider-driven updates, always use the provided sizeInKB parameter
  // and ignore the dataset.exactValue which is only for manual input tracking

  // Format based on size
  if (sizeInKB >= 1024) {
    const mbValue = sizeInKB / 1024;
    // If it's a whole number, display as integer
    if (mbValue === Math.floor(mbValue)) {
      return mbValue + "mb";
    }
    // Otherwise limit to 2 decimal places for display
    // Convert to fixed 2 decimal places
    let formattedValue = mbValue.toFixed(2);
    // Remove trailing zeros (e.g., 1.50 -> 1.5, 2.00 -> 2)
    formattedValue = formattedValue.replace(/\.?0+$/, "");
    return formattedValue + "mb";
  }

  // For KB values, also limit to 2 decimal places if needed
  if (sizeInKB === Math.floor(sizeInKB)) {
    return sizeInKB + "kb";
  } else {
    let formattedValue = parseFloat(sizeInKB).toFixed(2);
    formattedValue = formattedValue.replace(/\.?0+$/, "");
    return formattedValue + "kb";
  }
}

// Initialize slider on page load
document.addEventListener("DOMContentLoaded", initializeSlider);

// Make sure these are available globally
window.copyText = copyText;

window.handleSubmit = handleSubmit;
window.initializeSlider = initializeSlider;
window.formatSize = formatSize;

// Add this new function
function setupGlobalEnterHandler() {
  document.addEventListener("keydown", function (event) {
    if (event.key === "Enter" && !event.target.matches("textarea")) {
      const form = document.getElementById("ingestForm");
      if (form) {
        handleSubmit(new Event("submit"), true);
      }
    }
  });
}

// Add to the DOMContentLoaded event listener
document.addEventListener("DOMContentLoaded", () => {
  initializeSlider();
  setupGlobalEnterHandler();
});
