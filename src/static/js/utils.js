const MAXP = 500;
const MINV = Math.log(1);
const MAXV = Math.log(102400);

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

  // Check if slider is being used
  let isSliding = false;

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
  const value = Math.exp(MINV + (MAXV - MINV) * Math.pow(position / MAXP, 1.5));
  return value.toFixed(2);
}

// Move slider initialization to a separate function
function initializeSlider() {
  const slider = document.getElementById("file_size");
  const sizeValueInput = document.getElementById("size_value_input");

  // Set initial value using the `default_file_size` from server passed to the slider
  sizeValueInput.value = logSliderToSize(slider.value) + "kb";

  if (!slider || !sizeValueInput) return;

  // Check if we have an exact value from server response
  if (sizeValueInput.dataset.exactValue) {
    const exactValue = parseFloat(sizeValueInput.dataset.exactValue);
    setSliderPosition(exactValue);
  }

  // Extract numeric value from input
  function extractNumericValue() {
    const numericMatch = sizeValueInput.value
      .trim()
      .match(/^(\d+(?:\.\d+)?)\s*(kb|mb|k|m|)$/i);

    if (numericMatch) {
      let value = parseFloat(numericMatch[1]);
      const unit = numericMatch[2].toLowerCase();

      // Convert to KB
      if (unit === "m" || unit === "mb") {
        value = value * 1024;
      }
      return value;
    }
  }
  // Add input change handler for direct edits
  sizeValueInput.addEventListener("input", function () {
    isSliding = false;
    const value = extractNumericValue();

    // Update the exact value data attribute
    this.dataset.exactValue = value;
  });

  // Helper function to set slider position
  function setSliderPosition(value) {
    const position =
      MAXP * Math.pow((Math.log(value) - MINV) / (MAXV - MINV), 1 / 1.5);
    slider.value = position;
  }

  // Listen for keydown with "Enter" key
  sizeValueInput.addEventListener("keydown", function (event) {
    if (event.key === "Enter") {
      event.preventDefault();
      const value = extractNumericValue();
      setSliderPosition(value);
      updateSliderUI();
    }
  });
  sizeValueInput.addEventListener("focusout", function (event) {
    event.preventDefault();

    const value = extractNumericValue();
    setSliderPosition(value);
    updateSliderUI();
  });

  function updateSliderUI() {
    // Get the dataset value if it is set
    let exactValue;
    if (!isSliding) {
      exactValue = sizeValueInput.dataset.exactValue;
    } else {
      exactValue = logSliderToSize(slider.value);
    }

    // Update input value
    sizeValueInput.value =
      exactValue < 1024
        ? `${exactValue}kb`
        : `${(exactValue / 1024).toFixed(2)}mb`;
    sizeValueInput.dataset.exactValue = exactValue;
    // Update slider background
    slider.style.backgroundSize = `${(slider.value / slider.max) * 100}% 100%`;
  }

  // Remove input change handler to prevent interference with server value
  slider.addEventListener("input", function () {
    isSliding = true;
    updateSliderUI();
  });

  // Initialize slider position
  updateSliderUI();
}

// Add helper function for formatting size
function formatSize(sizeInKB) {
  // Convert to float to handle both string and number inputs
  const value = parseFloat(sizeInKB);

  // Format based on size
  if (value >= 1024) {
    const mbValue = value / 1024;
    // Return with exactly 2 decimal places
    return mbValue.toFixed(2).replace(/\.?0+$/, "") + "mb";
  }

  // For KB values
  return value.toFixed(2).replace(/\.?0+$/, "") + "kb";
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
