function saveOptions(e) {
  browser.storage.sync.set({
    colour: document.querySelector("#color").value
  });
  e.preventDefault();
}

function restoreOptions() {
  var gettingItem = browser.storage.sync.get('color');
  gettingItem.then((res) => {
    document.querySelector("#color").value = res.colour || 'Firefox red';
  });
}

document.addEventListener('DOMContentLoaded', restoreOptions);
document.querySelector("form").addEventListener("submit", saveOptions);
