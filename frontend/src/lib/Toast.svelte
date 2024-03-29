<script>
  import { flip } from "svelte/animate";
  import { fly } from "svelte/transition";
  import Fa from 'svelte-fa/src/fa.svelte';
  import { faCircleExclamation, faCircleInfo, faCircleCheck } from '@fortawesome/free-solid-svg-icons';
  import VisibilityChange from "svelte-visibility-change";
  import { notifications } from "./notifications.js";
  import Button from "$lib/Button.svelte";

  let hidden;
</script>

<div class="notifications">
{#each [...$notifications].reverse() as notification (notification.id)}
  <div class="toast flex-column" animate:flip in:fly={{ y: -30 }} out:fly>
    <div class="icon-and-text flex-row">
      {#if notification.type === "error"}
        <Fa icon={faCircleExclamation} size=2x color=red />
      {:else if notification.type === "success"}
        <Fa icon={faCircleCheck} size=2x color=green />
      {:else if notification.type === "info"}
        <Fa icon={faCircleInfo} size=2x color=blue />
      {/if}
      <div class="content">
        <div class="title">{notification.title}</div>
        <div class="message">{notification.message}</div>
        {#if notification.type === "error" && notification.options?.showFooter !== false}
          <div class="support">If the error persists please contact us via <a href="https://t.me/+XZmgmy8iLYFiZDRi" target=_blank>Telegram</a></div>
        {/if}
        {#if notification.options?.hasClose}
          <Button class=white on:click={notification.close} --font-size=12px --padding="5px 15px">Close</Button>
        {/if}
      </div>
    </div>
    <div class="progress" class:paused={hidden} style="--duration: {notification.options?.timeout || 3000}ms" on:animationstart={() => notification.isShown = true} on:animationend={notification.close}></div>
  </div>
{/each}
  <VisibilityChange bind:hidden />
</div>

<style>
.notifications {
  position: fixed;
  top: 88px;
  z-index: 101; /* should be more than header */
  display: flex;
  flex-direction: column;
  gap: 10px;
}
.toast {
  background: #FFFFFF;
  box-shadow: 0px 8px 20px rgba(185, 192, 204, 0.4);
  border-radius: 8px;
  width: 509px;
  max-width: 100vw;
  overflow: hidden;
}
.icon-and-text {
  gap: 19px;
  line-height: 20px;
  font-size: 14px;
  padding: 23px 21px 35px 17px;
}
.content {
  min-width: 0;
  display: flex;
  flex-direction: column;
  gap: 16px;
}
.message {
  overflow: auto;
  max-height: 400px;
  font-weight: 600;
}
.title {
  font-weight: 400;
  font-size: 14px;
}
.progress {
  height: 3px;
  animation: var(--duration) progress linear forwards;
  background: blue;
}
.support {
  font-size: 12px;
}
.toast:hover .progress,.toast:active .progress {
  animation-play-state: paused;
}
.progress.paused {
  animation-play-state: paused;
}
@keyframes progress {
  0% { width: 100%; }
  100% { width: 0; }
}
</style>
