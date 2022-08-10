async function handleMessage(request, sender, sendResponse) {
  let response;
  if (request.method === "get") {
    response = await fetch(request.url, {
      headers: {
        'Accept': 'application/json'
      }
    });
  } else if (request.method === "post") {
    response = await fetch(request.url, {
      method: 'POST',
      headers: {
        'Accept': 'application/json',
        'Content-Type': 'application/json'
      },
      body: JSON.stringify(request.data)
    });
  } else {
    console.log(`Unexpected method ${request.method}`);
    return;
  }
  if (response.status !== 200) {
    sendResponse({status: "error", response: response});
  } else {
    sendResponse({status: "success", response: await response.json()});
  }
}


async function init() {
  chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
    handleMessage(request, sender, sendResponse);
    return true;
  });
  browser.browserAction.onClicked.addListener((ev) => {
    browser.runtime.openOptionsPage();
  });

  /*
  const registration = await navigator.serviceWorker.register('/serviceworker.js');
  const subscription = await registration.pushManager.subscribe({
    userVisibleOnly: true,
    applicationServerKey: 'asd',
  });
  console.log(subscription);*/
}

init();
