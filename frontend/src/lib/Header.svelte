<script>
  import { Link, link } from "svelte-navigator";
  import Logo from "$lib/Logo.svelte";
  import Social from "$lib/Social.svelte";
  import Userpic from "$lib/Userpic.svelte";
  import WalletLogin from "$lib/WalletLogin.svelte";
  import ClaimPopup from "$lib/ClaimPopup.svelte";
  import Amount from "$lib/Amount.svelte";
  import { syncMe as me } from "$lib/session.js";
  import { resolve } from "$lib/utils.js";

  export let simple = false;

  let showMenu = false;
  let showClaim = false;
</script>

<!-- svelte-ignore a11y-click-events-have-key-events -->
<div class="menu-popup" on:click={() => { showMenu = false; }} style:visibility={showMenu ? "visible" : "hidden"}>
  <div class="menu-header">
    <a use:link href="/"><Logo /></a>
    <div class="menu-close-button"><img src="/static/burger_back.svg" alt="back"></div>
  </div>
  <nav>
    <ul>
      <li><a href="https://github.com/Donate4Fun/donate4fun/blob/master/docs/HELP.md" target="_blank">Docs</a></li>
      <li><a href="https://github.com/orgs/Donate4Fun/projects/1" target="_blank">Roadmap</a></li>
      <li><a use:link href="/#team">Team</a></li>
      {#if $me}
        <li><a use:link href="/donator/{$me.donator.id}">Profile</a></li>
        {#if $me.connected}
          <li><a use:link href="/settings">Settings</a></li>
        {:else}
          <li><a use:link href="/signin">Sign in</li>
        {/if}
      {/if}
    </ul>
  </nav>
</div>
<ClaimPopup bind:show={showClaim} />
<header>
  <div class="logo">
    <a use:link href="/"><Logo /></a>
  </div>
  <nav class="quick-links">
    <a target=_blank href="https://github.com/orgs/Donate4Fun/projects/1">Roadmap</a>
    <a target=_blank href="https://github.com/Donate4Fun/donate4fun/blob/master/docs/HELP.md">Docs</a>
    {#if !simple}
      <a href={'#'} on:click={() => {showClaim = true; return false;}}>Claim donations</a>
    {/if}
  </nav>
  <div class="right">
    {#if $me}
      <div class="amount">
        {#if $me.connected}
          <Amount amount={$me.donator.balance} />
        {:else}
          <a use:link href="/signin">Sign In</a>
        {/if}
      </div>
    {/if}
    <div class="userpic">
      {#if $me}
        <Userpic user={$me.donator} />
      {/if}
    </div>
    <!-- svelte-ignore a11y-click-events-have-key-events -->
    <div class="menu-button" on:click={() => { showMenu = true; }}><img src="/static/Burger.svg" alt="burger"></div>
  </div>
</header>

<style>
header {
  display: flex;
  align-items: center;
  place-content: space-between;
  width: 100%;
  box-sizing: border-box;
  font-size: 15px;
  position: sticky;
  top: 0;
  z-index: 100;
  background: rgba(247, 249, 255, 0.8);
  backdrop-filter: blur(12px);
  box-shadow: 0px 1px 0px rgba(0, 0, 0, 0.05);
  transition: ease 0.3s;
}
.userpic {
  --width: 48px;
  --size: 48px;
}
.menu-popup {
  position: fixed;
  width: 100vw;
  height: 100vh;
  display: flex;
  flex-direction: column;
  z-index: 101;
  background: #F7F9FF;
}
.menu-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  height: 88px;
  padding-left: 28px;
  padding-right: 40px;
}
.menu-button,.menu-close-button {
  cursor: pointer;
}
.menu-popup ul {
  list-style-type: none;
  display: flex;
  flex-direction: column;
  align-items: center;
}
.menu-popup li {
  height: 48px;
  width: 100%;
  display: flex;
  justify-content: center;
}
.menu-popup li a {
  width: 100%;
  display: flex;
  justify-content: center;
  align-items: center;
}
@media (max-width: 640px) {
  .amount {
    display: none;
  }
  header {
    padding-left: 18px;
    padding-right: 24px;
    height: 72px;
  }
}
@media (min-width: 641px) {
  header {
    padding-left: 28px;
    padding-right: 40px;
    height: 88px;
    gap: 56px;
  }
}
@media (max-width: 1000px) {
  .quick-links {
    display: none;
  }
}
@media (min-width: 1001px) {
  .menu-button {
    display: none;
  }
  .quick-links {
    display: flex;
    align-items: center;
    justify-content: end;
    flex-grow: 1;
    gap: 40px;
  }
}
.right {
  display: flex;
  align-items: center;
  gap: 32px;
  font-weight: 700;
}
.menu-popup ul {
  padding: 0;
}
.quick-links a, .menu-popup ul a, .right a {
  font-size: 15px;
  line-height: 18px;
  text-align: center;
  letter-spacing: 0.01em;
  color: var(--color);
}
</style>
