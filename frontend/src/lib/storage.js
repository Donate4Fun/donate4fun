export const storage = new Proxy({}, {
  get(obj, prop) {
    return window.localStorage.getItem(prop);
  },
  set(obj, prop, value) {
    window.localStorage.setItem(prop, value);
    return true;
  }
});
