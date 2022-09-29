export const storage = new Proxy({}, {
  get(obj, prop) {
    return JSON.parse(window.localStorage.getItem(prop));
  },
  set(obj, prop, value) {
    window.localStorage.setItem(prop, JSON.stringify(value));
    return true;
  }
});
