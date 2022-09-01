import { writable, derived } from "svelte/store";

const notifications = writable([]);

function notify(title, message, type = "default", timeout = 300000) {
  notifications.update(state => {
    const id_ = id();

    function close() {
      notifications.update(state => {
        return state.filter(notification => notification.id !== id_);
      });
    }

    setTimeout(close, timeout);

    return [...state, { id: id_, type, title, message, close }];
  });
}

function id() {
  return '_' + Math.random().toString(36).substr(2, 9);
}

export { notifications, notify };
