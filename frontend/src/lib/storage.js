export const storage = new Proxy({}, {
  get: (obj, prop) => {
    // localStorage is not available in Firefox Add-on and sessionStorage actually persists
    // between Popup reopens
    const storage = window.localStorage || window.sessionStorage;
    return JSON.parse(storage.getItem(prop));
  },
  set: (obj, prop, value) => {
    const storage = window.localStorage || window.sessionStorage;
    storage.setItem(prop, JSON.stringify(value));
    return true;
  }
});
