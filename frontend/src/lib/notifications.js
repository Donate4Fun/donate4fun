import { writable, derived, get } from "svelte/store";
import { globalHistory } from "svelte-navigator";

const notifications = writable([]);

function notify(title, message, type = "error", options = null) {
  notifications.update(state => {
    const id_ = id();

    function close() {
      notifications.update(state => {
        return state.filter(notification => notification.id !== id_);
      });
    }

    return [...state, { id: id_, type, title, message, close, options, isShown: false }];
  });
}

function id() {
  return '_' + Math.random().toString(36).substr(2, 9);
}

globalHistory.listen(() => {
  for (const notification of get(notifications)) {
    if (notification.isShown)
      notification.close()
  }
});

export { notifications, notify };
