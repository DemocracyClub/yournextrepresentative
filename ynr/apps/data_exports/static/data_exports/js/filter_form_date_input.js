// Split up date inputs for easier UX
const DateInput = document.querySelector('input[name="election_date"]');
DateInput.type = "hidden";
DateInput.insertAdjacentHTML("afterend", `
    <div class="row">
      <div class="large-4 columns">
        <label for="election_date_day">
          Day
        </label>
        <input type="text" id="election_date_day" inputmode="numeric" pattern="^(0?[1-9]|[12]\\d|3[01]|\\*)?$" >
      </div>
      <div class="large-4 columns">
        <label for="election_date_month">
          Month
        </label>
        <input type="text" id="election_date_month" inputmode="numeric" pattern="^(0?[1-9]|1[0-2]|\\*)?$">
      </div>
      <div class="large-4 columns">
        <label for="election_date_year">
          Year
        </label>
        <input type="text" id="election_date_year" inputmode="numeric" pattern="^(\\d{4}|\\*)?$">
    </div>
  </div>
`);
const dayInput = document.getElementById('election_date_day');
const monthInput = document.getElementById('election_date_month');
const yearInput = document.getElementById('election_date_year');

const reDate = /^([^-]+)-([^-]+)-([^-]+)$/;
if (DateInput.value) {
  const match = DateInput.value.match(reDate);
  if (match) {
    // match[1], match[2], match[3] are year, month, day (based on your existing format)
    const [_, y, m, d] = match;
    yearInput.value = (y === '.*') ? '' : y.replace(/^\.\*/, '*');   // If it was .*, show '*'
    monthInput.value = (m === '.*') ? '' : m.replace(/^\.\*/, '*');
    dayInput.value = (d === '.*') ? '' : d.replace(/^\.\*/, '*');
  }
}

const filter_form = DateInput.closest('form');

filter_form.addEventListener('submit', function (e) {
  e.preventDefault();  // stop the normal GET

  let d = dayInput.value.trim() || '*';
  let m = monthInput.value.trim() || '*';
  let y = yearInput.value.trim() || '*';

  function toRegexPart(val, zero_pad = false) {
    if (!val || val === '') {
      return '.*'; // blank => wildcard
    }
    if (val === '*') {
      return '.*'; // single star => wildcard
    }
    if (zero_pad) {
      // We assume only digits or '*' are allowed, due to HTML pattern.
      const n = parseInt(val, 10);
      // If parse fails, just return original
      if (isNaN(n)) return val;
      return String(n).padStart(2, '0');
    }
    // For year: if digits, we keep them as-is.
    // (If you want to ensure it's 4 digits, it's enforced by pattern anyway.)
    return val;
  }

  d = toRegexPart(d, true);
  m = toRegexPart(m, true);
  y = toRegexPart(y, false);
  // Combine them into ISO-like "YYYY-MM-DD"
  DateInput.value = `${y}-${m}-${d}`;
  if (DateInput.value === ".*-.*-.*") {
    DateInput.value = "";
  }


  // Create a new URLSearchParams object from the existing query parameters
  const existingParams = new URLSearchParams(window.location.search);
  var newParams = new URLSearchParams(existingParams);

  const formData = new FormData(filter_form);

  // Remove 'page' param if it exists
  newParams.delete('page');

  // Update newParams with form data (overwriting or adding)
  for (const [key, value] of formData.entries()) {
    newParams.set(key, value);
  }

  // Remove any params with empty values
  for (const [key, value] of Array.from(newParams.entries())) {
    if (value.toString().trim() === '') {
      newParams.delete(key);
    }
  }

  // Build the new URL and navigate
  const url = new URL(filter_form.action, location.href);
  url.search = newParams.toString();
  window.location.href = url.toString();

});
