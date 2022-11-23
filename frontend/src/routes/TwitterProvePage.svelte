<script>
  import Section from "$lib/Section.svelte";
  import Editable from "$lib/Editable.svelte";
  import CopyButton from "$lib/CopyButton.svelte";
  import Button from "$lib/Button.svelte";
  import TwitterAccount from "$lib/TwitterAccount.svelte";
  import { me, reloadMe } from "$lib/session.js";
  import { sleep } from "$lib/utils.js";
  import api from "$lib/api.js";
  import title from "$lib/title.js";

  export let navigate;

  async function check() {
    await sleep(5000);
    await api.post("me/twitter/check-ownership");
    await reloadMe();
    checkPressed = true;
  }

  async function loadProveMessage() {
    return (await api.get("twitter/ownership-message")).message;
  }

  async function loadLinkedTwitterAccounts() {
    return (await api.get("twitter/linked"));
  }

  title.set("Link Twitter account");
</script>

<Section>
  <main>
    <h1>Prove that you own a Twitter channel</h1>
    <summary>
      {#await loadProveMessage() then proveMessage}
        <span><a href="https://twitter.com/messages/compose?recipient_id=1572908920485576704&text={proveMessage}" target=_blank>Send a magic direct message</a> to our account and wait for a reply.</span>
      {/await}
    </summary>
    <div>
      {#await loadLinkedTwitterAccounts() then twitter_accounts}
        {#if twitter_accounts.length}
          <h2>Linked channels</h2>
          {#each twitter_accounts as twitter_account}
            <TwitterAccount account={twitter_account} />
          {/each}
        {/if}
      {/await}
    </div>
    <Button class="grey" on:click={() => navigate(-1)}>Back</Button>
  </main>
</Section>

<style>
main {
  display: flex;
  flex-direction: column;
  gap: 32px;
  padding: 36px 85px 40px 85px;
  width: 640px;
  font-size: 16px;
  line-height: 19px;
}
h1 {
  text-align: center;
  margin: 0;
}
h2 {
  font-weight: 600;
  font-size: 11px;
  text-transform: uppercase;
  color: rgba(0, 0, 0, 0.8);
  margin: 0;
}
</style>
