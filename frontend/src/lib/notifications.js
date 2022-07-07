import { writable, derived } from "svelte/store";

const notifications = writable([]);

function notify(title, message, type = "default", timeout = 3000) {
  notifications.update(state => {
    const id_ = id();
    setTimeout(() => {
      notifications.update(state => {
        return state.filter(notification => notification.id !== id_);
      });
    }, timeout);

    return [...state, { id: id_, type, title, message }];
  });
}

function id() {
  return '_' + Math.random().toString(36).substr(2, 9);
}

export { notifications, notify };
