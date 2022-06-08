<script>
  import Section from "../lib/Section.svelte";
  import Input from "../lib/Input.svelte";
  import Button from "../lib/Button.svelte";
  import axios from "axios";

  let donatee;

  const claim = async () => {
    const resp = await axios.get(`/api/v1/donatee`, {donatee: donatee})
    resp.json()
  }
</script>

<Section>
  <h1>Claim donations</h1>
  <p>Check if your channel have been donated, just paste your Channel’s URL</p>
  <p class="controls">
    <Input placeholder="Paste your Youtube channel’s URL" bind:value={donatee}/>
    <Button disabled={!donatee} on:click={claim}>Check donation</Button>
  <div>
</Section>

<style>
.controls {
  display: flex;
  align-items: center;
  margin-left: -10px;
}
:global(button) {
  white-space: nowrap;
}
</style>
