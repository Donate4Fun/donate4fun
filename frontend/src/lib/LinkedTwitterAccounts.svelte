<script>
  import TwitterAccount from "$lib/TwitterAccount.svelte";
  import ChannelLogo from "$lib/ChannelLogo.svelte";
  import Button from "$lib/Button.svelte";
  import Amount from "$lib/Amount.svelte";
  import api from "$lib/api.js";

  export let accounts;

  async function take(account) {
    await api.post(`/twitter/account/${account.id}/transfer`);
    await load();
  }

  async function load() {
    accounts = await api.get("twitter/linked-accounts");
  }
</script>

<div class="container">
  <div class="header">
    <h2>Linked Twitter accounts</h2>
    <Button --width=70px link="/twitter/prove">Add</Button>
  </div>
  {#await load() then}
    <ul>
      {#each accounts as account}
      <li>
        <div class="channel-name">
          <TwitterAccount linkto=withdraw account={account} />
        </div>
        <Amount amount={account.balance} />
        <div class="withdraw-button">
          <Button disabled={account.balance === 0} on:click={() => take(account)} --border-width=0>Take</Button>
        </div>
      </li>
      {/each}
    </ul>
  {/await}
</div>

<style>
.container {
  width: 100%;
}
.header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}
ul {
  display: flex;
  flex-direction: column;
  width: 100%;
  gap: 8px;
  padding: 0;
}
li {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 17px;
  padding: 16px;
  height: 72px;
  background: linear-gradient(90deg, rgba(157, 237, 162, 0.15) 0%, rgba(157, 237, 162, 0) 100%);
  border-radius: 8px;
}
.withdraw-button {
  width: 136px;
  height: 44px;
  justify-self: end;
}
.channel-name {
  width: 100%;
}
</style>
