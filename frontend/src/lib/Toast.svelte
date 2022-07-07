<script>
  import { flip } from "svelte/animate";
  import { fly } from "svelte/transition";
  import { notifications } from "./notifications.js";

  export let title = null;
  export let message = null;
</script>

<div class="notifications">
{#each [...$notifications].reverse() as notification (notification.id)}
  <div class="toast" animate:flip in:fly={{ y: -30 }} out:fly>
    <img src="/exclamation-red.svg" alt="exclamation">
    <div class="text">
      <div class="title">{notification.title}</div>
      <div class="message">{notification.message}</div>
      <div class="support">Contact us in <a href="https://discord.gg/VvqUaFeQZU">Discord</a> or <a href="https://t.me/+XZmgmy8iLYFiZDRi">Telegram</a></div>
    </div>
  </div>
{/each}
</div>

<style>
.notifications {
  position: fixed;
  top: 88px;
  z-index: 10;
  display: flex;
  flex-direction: column;
  gap: 10px;
}
.toast {
  display: flex;
  flex-direction: row;
  gap: 19px;
  background: #FFFFFF;
  box-shadow: 0px 8px 20px rgba(185, 192, 204, 0.4);
  border-radius: 8px;
  padding-top: 23px;
  padding-right: 21px;
  padding-left: 17px;
  padding-bottom: 35px;
  line-height: 20px;
  font-size: 14px;
  width: 509px;
}
img {
  margin-top: 9px;
  width: 24px;
  height: 24px;
}
.title {
  font-weight: 700;
  font-size: 16px;
  margin-bottom: 12px;
}
</style>
