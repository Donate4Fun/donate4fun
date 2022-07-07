<script>
  import { navigate } from "svelte-navigator";

  import Section from "../lib/Section.svelte";
  import Input from "../lib/Input.svelte";
  import Button from "../lib/Button.svelte";
  import Spinner from "../lib/Spinner.svelte";
  import api from "../lib/api.js";

  let donatee;
  let spin = false;
  let error = null;

  async function claim() {
    spin = true;
    error = null;
    try {
      const channel = await api.post(`donatee`, {target: donatee})
      navigate(`/youtube/${channel.id}`);
    } catch (exc) {
      console.error(exc);
      error = exc.error;
    }
    spin = false;
  }
</script>

<Section class="claim">
  <h1>Claim donations</h1>
  <span>Check if your channel have been donated, just paste your Channel’s URL</span>
  <form on:submit|preventDefault={claim}>
    <div class=url><Input type=url placeholder="Paste YouTube URL" bind:value={donatee} bind:error={error} logo=url(/youtube.svg) /></div>
    <Button disabled={!donatee} type=submit class="submit white">
      {#if spin}
      <Spinner class="spinner" size=20px width=3px/>
      {/if}
      Check donation
    </Button>
  </form>
</Section>

<style>
@media (max-width: 640px) {
  :global(.claim) {
    width: 100%;
    padding: 20px 36px 20px 24px;
  }
  form {
    margin-top: 42px;
  }
  form .url {
    width: 100%;
    margin-bottom: 24px;
  }
  form :global(.submit) {
    width: 100%;
    margin-bottom: 25px;
  }
}
h1 {
  margin-top: 0px;
  margin-bottom: 16px;
}
span {
  font-size: 14px;
  line-height: 17px;
}
@media (min-width: 641px) {
  :global(.claim) {
    width: 640px;
    padding: 36px 36px 40px 36px;
  }
  form {
    display: flex;
    align-items: center;
    margin-top: 38px;
  }
  form .url {
    width: 365px;
    margin-right: 24px;
  }
  form :global(button) {
    white-space: nowrap;
    width: 180px;
  }
}
</style>
