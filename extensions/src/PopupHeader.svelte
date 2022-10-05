<script>
  import {get} from 'svelte/store';
  import { useNavigate } from "svelte-navigator";
  import Fa from 'svelte-fa/src/fa.svelte';
  import {faGear, faGlobe, faSyringe, faComment, faWindowRestore, faHashtag} from '@fortawesome/free-solid-svg-icons';
  import {me} from "$lib/session.js";
  import {apiOrigin} from "$lib/api.js";
  import Userpic from "$lib/Userpic.svelte";
  import Amount from "$lib/Amount.svelte";
  import FiatAmount from "$lib/FiatAmount.svelte";
  import Button from "$lib/Button.svelte";
  import WalletLogin from "$lib/WalletLogin.svelte";
  import MeNamePubkey from "$lib/MeNamePubkey.svelte";
  import MeBalance from "$lib/MeBalance.svelte";
  import DonateYoutube from "./DonateYoutube.svelte";
  import { worker, browser, connectToPage, createPopup } from "./common.js";
  import cLog from "./log.js";

  export let history;

  let balance;
  let popupVisible = false;
  let showDev = false;
  let contentScript;
  const iconColor = '#787981';

  async function load() {
    await $me.loaded;
    showDev = await worker.getConfig('enableDevCommands');
    balance = $me.donator.balance;
  }

  async function loadDev() {
    try {
      contentScript = await connectToPage();
    } catch (error) {
      cLog("could not connect to page", error);
    }
  }
</script>

<main class="flex-column gap-41">
  {#await load() then}
    <header class="flex-row justify-space-between">
      <img src="static/D.svg" width=40px alt=D class=text />
      <MeNamePubkey />
      <Userpic user={$me.donator} target=_blank --width=44px />
      <div on:click={() => popupVisible = !popupVisible} class="flex-row align-center justify-center position-relative cursor-pointer">
        <svg width="44" height="44" viewBox="0 0 44 44" fill="none" xmlns="http://www.w3.org/2000/svg">
          <circle cx="22" cy="22" r="21.5" stroke="black" stroke-opacity="0.1"/>
          <circle cx="22" cy="15" r="2" fill="black"/>
          <circle cx="22" cy="22" r="2" fill="black"/>
          <circle cx="22" cy="29" r="2" fill="black"/>
        </svg>
        {#if popupVisible}
          <div class="popup flex-column user-select-none">
            <div on:click={() => browser.runtime.openOptionsPage()}>
              <Fa icon={faGear} size=2x color={iconColor} />
              <span>Settings</span>
            </div>
            <a class="text-decoration-none" href="https://donate4.fun" target="_blank">
              <Fa icon={faGlobe} size=2x color={iconColor} />
              <span>Website</span>
            </a>
            {#if showDev}
              {#await loadDev() then}
                <div disabled={!contentScript} on:click={() => contentScript.postComment("en", 100)}>
                  <Fa icon={faComment} size=2x color={iconColor} />
                  <span>Insert comment</span>
                </div>
                <div disabled={!contentScript} on:click={() => contentScript.onPaid({amount: 333})}>
                  <Fa icon={faComment} size=2x color={iconColor} />
                  <span>Show comment popup</span>
                </div>
                <div on:click={connectToPage}>
                  <Fa icon={faSyringe} size=2x color={iconColor} />
                  <span>Inject script</span>
                </div>
                <div on:click={createPopup}>
                  <Fa icon={faWindowRestore} size=2x color={iconColor} />
                  <span>Create popup window</span>
                </div>
                <div on:click={() => history.navigate('/nowebln/1000')}>
                  <Fa icon={faHashtag} size=2x color={iconColor} />
                  <span>Open NoWebLN page</span>
                </div>
              {/await}
            {/if}
          </div>
        {/if}
      </div>
    </header>
    <div class="flex-column gap-20 align-center">
      {#if $me.connected}
        <MeBalance />
      {:else}
        <WalletLogin target=_blank />
      {/if}
    </div>
  {/await}
</main>

<style>
main {
  padding: 27px 32px 0 27px;
}
.popup {
  width: 200px;
  background: #FFFFFF;
  border: 1px solid #E7E7E7;
  box-shadow: 10px 15px 20px rgba(209, 217, 230, 0.15);
  border-radius: 12px;
  top: 0;
  right: 100%;
  visibility: visible;
}
.popup > div,a {
  height: 48px;
  font-size: 12px;
  font-weight: 500;
  padding: 12px 20px;
  display: flex;
  gap: 12px;
  align-items: center;
}
.popup span:nth-child(1) {
  font-size: 30px;
  color: #787981;
}
.popup > div:hover,a:hover {
  background: #F7F8FF;
  height: 48px;
}
</style>
