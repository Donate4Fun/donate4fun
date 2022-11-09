<script>
  import {get} from 'svelte/store';
  import { useNavigate } from "svelte-navigator";
  import Fa from 'svelte-fa/src/fa.svelte';
  import { faGear, faGlobe, faSyringe, faComment, faWindowRestore, faHashtag } from '@fortawesome/free-solid-svg-icons';
  import { me } from "$lib/session.js";
  import Userpic from "$lib/Userpic.svelte";
  import Amount from "$lib/Amount.svelte";
  import FiatAmount from "$lib/FiatAmount.svelte";
  import Button from "$lib/Button.svelte";
  import MeNamePubkey from "$lib/MeNamePubkey.svelte";
  import MeBalance from "$lib/MeBalance.svelte";
  import { worker, browser, connectToPage, createPopup } from "./common.js";
  import cLog from "$lib/log.js";
  import { resolve } from "$lib/utils.js";

  let navigate = useNavigate();
  let popupVisible = false;
  const iconColor = '#787981';
</script>

<div class="main">
  {#await me.get() then me}
    <header>
      <img src="static/D.svg" width=28px alt=D class=text />
      <div class="name">
        <MeNamePubkey />
      </div>
      <Userpic user={me.donator} target=_blank --width=44px />
      <div on:click={() => popupVisible = !popupVisible} class="flex-row align-center justify-center position-relative cursor-pointer">
        <svg width="44" height="44" viewBox="0 0 44 44" fill="none" xmlns="http://www.w3.org/2000/svg">
          <circle cx="22" cy="22" r="21.5" stroke="black" stroke-opacity="0.1"/>
          <circle cx="22" cy="15" r="2" fill="black"/>
          <circle cx="22" cy="22" r="2" fill="black"/>
          <circle cx="22" cy="29" r="2" fill="black"/>
        </svg>
        <div class="popup flex-column user-select-none" class:popupVisible>
          <div on:click={() => browser.runtime.openOptionsPage()}>
            <Fa icon={faGear} size=2x color={iconColor} />
            <span>Settings</span>
          </div>
          <a class="text-decoration-none" href="https://donate4.fun" target="_blank">
            <Fa icon={faGlobe} size=2x color={iconColor} />
            <span>Website</span>
          </a>
          {#await worker.getConfig('enableDevCommands') then showDev}
            {#if showDev}
              {#await connectToPage() then contentScript}
                <div on:click={() => contentScript.postComment("en", 100)}>
                  <Fa icon={faComment} size=2x color={iconColor} />
                  <span>Insert comment</span>
                </div>
                <div on:click={() => contentScript.onPaid({amount: 333})}>
                  <Fa icon={faComment} size=2x color={iconColor} />
                  <span>Show comment popup</span>
                </div>
              {/await}
              <div on:click={connectToPage}>
                <Fa icon={faSyringe} size=2x color={iconColor} />
                <span>Inject script</span>
              </div>
              <div on:click={createPopup}>
                <Fa icon={faWindowRestore} size=2x color={iconColor} />
                <span>Create popup window</span>
              </div>
              <div on:click={() => navigate('/nowebln/1000/false')}>
                <Fa icon={faHashtag} size=2x color={iconColor} />
                <span>Open no WebLN page</span>
              </div>
              <div on:click={() => navigate('/nowebln/1000/true')}>
                <Fa icon={faHashtag} size=2x color={iconColor} />
                <span>Open WebLN rejected page</span>
              </div>
            {/if}
          {/await}
        </div>
      </div>
    </header>
    <div class="flex-column gap-20 align-center">
      {#if me.connected}
        <MeBalance />
      {:else}
        <p>Do you want faster payments and zero fees?</p>
        <Button link={resolve('/login')} class="white" target=_blank>
          Connect wallet and fulfill balance
        </Button>
      {/if}
    </div>
  {:catch err}
    Error whlie loading session: {err}.
  {/await}
</div>

<style>
.main {
  padding: 32px 32px 0;

  display: flex;
  flex-direction: column;
  gap: 32px;
}
header {
  display: flex;
  gap: 16px;
  justify-content: space-between;
}
.name {
  flex-grow: 2;
  display: flex;
  justify-content: center;
  min-width: 0;
}
.popup {
  width: 200px;
  background: #FFFFFF;
  border: 1px solid #E7E7E7;
  box-shadow: 10px 15px 20px rgba(209, 217, 230, 0.15);
  border-radius: 12px;
  top: 0;
  right: 100%;
  visibility: hidden;
  opacity: 0;
  position: absolute;
  transition: all 0.2s ease;
}
.popupVisible {
  visibility: visible;
  opacity: 1;
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
