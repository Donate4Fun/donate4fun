<script>
  import { Link, link } from "svelte-navigator";
  import Logo from "$lib/Logo.svelte";
  import Social from "$lib/Social.svelte";
  import Userpic from "$lib/Userpic.svelte";
  import Spinner from "$lib/Spinner.svelte";
  import Button from "$lib/Button.svelte";
  import WalletLogin from "$lib/WalletLogin.svelte";
  import { me } from "$lib/session.js";
  import { resolve } from "$lib/utils.js";

  let showMenu = false;
</script>

<div class="menu-popup" on:click={() => { showMenu = false; }} style:visibility={showMenu ? "visible" : "hidden"}>
  <div class="menu-header">
    <a use:link href="/"><Logo /></a>
    <div class="menu-close-button"><img src="/static/burger_back.svg" alt="back"></div>
  </div>
  <nav>
    <ul>
      <li><a href="https://github.com/Donate4Fun/donate4fun/blob/master/docs/HELP.md" target="_blank">Docs</a></li>
      <li><a href="https://github.com/orgs/Donate4Fun/projects/1" target="_blank">Roadmap</a></li>
      <li><a use:link href="/prove/youtube">Claim donations</a></li>
      <li><a use:link href="/login">Connect wallet</li>
      <li><a use:link href="/#team">Team</a></li>
      {#await $me then me}
        <li><a use:link href="/donator/{me.donator.id}">Profile</a></li>
      {/await}
    </ul>
  </nav>
</div>
<header>
  <div class="logo">
    <a use:link href="/"><Logo /></a>
  </div>
  <nav class="quick-links">
    <a target=_blank href="https://github.com/orgs/Donate4Fun/projects/1">Roadmap</a>
    <a target=_blank href="https://github.com/Donate4Fun/donate4fun/blob/master/docs/HELP.md">Docs</a>
    <a use:link href="/prove/youtube">Claim donations</a>
  </nav>
  <div class="right">
    <div class="connect-button">
      <WalletLogin />
    </div>
    <div class="userpic">
      {#await $me then me}
        <Userpic user={me.donator} />
      {:catch err}
        <p>Catch {err}</p>
      {/await}
    </div>
    <div class="menu-button" on:click={() => { showMenu = true; }}><img src="/static/Burger.svg" alt="burger"></div>
  </div>
</header>

<style>
header {
  display: flex;
  align-items: center;
  gap: 56px;
  place-content: space-between;
  width: 100%;
  height: 88px;
  box-sizing: border-box;
  font-size: 15px;
  position: sticky;
  top: 0;
  z-index: 100;
  background: rgba(247, 249, 255, 0.8);
  backdrop-filter: blur(12px);
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
  .connect-button {
    display: none;
  }
  header {
    padding-left: 18px;
    padding-right: 24px;
  }
}
@media (min-width: 641px) {
  .connect-button {
    width: 204px;
    --padding: 11px 22px;
  }
  header {
    padding-left: 28px;
    padding-right: 40px;
  }
}
@media (max-width: 1000px) {
  .quick-links {
    display: none;
  }
  .connect-button {
    width: 180px;
    font-size: 15px;
    line-height: 18px;
    --padding: 11px 20px;
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
.quick-links a, .menu-popup ul a {
  font-size: 15px;
  line-height: 18px;
  text-align: center;
  letter-spacing: 0.01em;
  color: var(--color);
}
</style>
