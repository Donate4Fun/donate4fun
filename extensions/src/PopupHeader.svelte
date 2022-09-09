<script>
  import {get} from 'svelte/store';
  import Fa from 'svelte-fa/src/fa.svelte';
  import {faGear, faGlobe, faSyringe, faComment, faWindowRestore} from '@fortawesome/free-solid-svg-icons';
  import {me} from "../../frontend/src/lib/session.js";
  import {apiOrigin} from "../../frontend/src/lib/api.js";
  import Userpic from "../../frontend/src/lib/Userpic.svelte";
  import Amount from "../../frontend/src/lib/Amount.svelte";
  import FiatAmount from "../../frontend/src/lib/FiatAmount.svelte";
  import Button from "../../frontend/src/lib/Button.svelte";
  import WalletLogin from "../../frontend/src/lib/WalletLogin.svelte";
  import DonateYoutube from "./DonateYoutube.svelte";
  import {worker, browser, contentScript, createPopup} from "./common.js";

  const fulfillLink = get(apiOrigin) + '/fulfill/' + get(me).donator.id;
  let popupVisible = false;
  let showDev = false;
  const iconColor = '#787981';

  async function load() {
    showDev = await worker.getConfig('enableDevCommands');
  }

</script>

<main class="flex-column gap-41">
  <header class="flex-row justify-space-between">
    <img class=text src="/static/D.svg" alt="D" width=40px>
    <div class="flex-column gap-10">
      <p class="font-15 margin-0">{$me.donator.name}</p>
      {#if $me.donator.lnauth_pubkey}
        <p class="flex-row gap-6 font-12 font-weight-300 margin-0">Connected wallet: <span class="ellipsis font-weight-600">{$me.shortkey}</span></p>
      {/if}
    </div>
    <Userpic user={$me.donator} />
  </header>
  {#await load() then}
  <div class="flex-column gap-20 align-center">
    {#if $me.donator.lnauth_pubkey}
      <div class="flex-column gap-12 width-full">
        <div class="amount-and-dots">
          <Amount class="font-24 font-weight-700i grid-column-2 text-align-center" amount={$me.donator.balance} />
          <div on:click={() => popupVisible = !popupVisible} class="flex-row align-center justify-center position-relative cursor-pointer">
            <svg width="4" height="18" viewBox="0 0 4 18" fill="none" xmlns="http://www.w3.org/2000/svg">
              <circle cx="2" cy="2" r="2" fill="black"/>
              <circle cx="2" cy="9" r="2" fill="black"/>
              <circle cx="2" cy="16" r="2" fill="black"/>
            </svg>
            <div class="popup flex-column" class:popupVisible>
              <div on:click={() => browser.runtime.openOptionsPage()}>
                <Fa icon={faGear} size=2x color={iconColor} />
                <span>Settings</span>
              </div>
              <a class="text-decoration-none" href="https://donate4.fun" target="_blank">
                <Fa icon={faGlobe} size=2x color={iconColor} />
                <span>Website</span>
              </a>
              {#if showDev}
                <div on:click={() => contentScript.postComment("en", 100)}>
                  <Fa icon={faComment} size=2x color={iconColor} />
                  <span>Insert comment</span>
                </div>
                <div on:click={() => worker.injectContentScript()}>
                  <Fa icon={faSyringe} size=2x color={iconColor} />
                  <span>Inject script</span>
                </div>
                <div on:click={createPopup}>
                  <Fa icon={faWindowRestore} size=2x color={iconColor} />
                  <span>Create popup</span>
                </div>
              {/if}
            </div>
          </div>
        </div>
        <FiatAmount class="font-12 font-weight-400 text-align-center" amount={$me.donator.balance} />
      </div>
      <Button target=_blank link={fulfillLink} class=white>Fulfill</Button>
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
.amount-and-dots {
  display: grid;
  grid-template-columns: 10% 80% 10%;
}
.popup {
  width: 200px;
  background: #FFFFFF;
  border: 1px solid #E7E7E7;
  box-shadow: 10px 15px 20px rgba(209, 217, 230, 0.15);
  border-radius: 12px;
  top: 0;
  right: 100%;
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
.popup.popupVisible {
  visibility: visible;
}
</style>
