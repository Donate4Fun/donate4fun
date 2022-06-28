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

<Section class="claim">
  <h1>Claim donations</h1>
  <span>Check if your channel have been donated, just paste your Channel’s URL</span>
  <form>
    <Input placeholder="Paste your Youtube channel’s URL" bind:value={donatee}/>
    <Button disabled={!donatee} on:click={claim}>Check donation</Button>
  </form>
</Section>

<style>
:global(.claim) {
  padding: 36px 36px 40px 36px;
  display: flex;
  flex-direction: column;
  width: 718px;
  height: 216px;
  box-sizing: border-box;
}
h1 {
  margin-top: 0px;
  margin-bottom: 16px;
}
span {
  font-size: 14px;
  line-height: 17px;
}
form {
  display: flex;
  align-items: center;
  margin-top: 38px;
  gap: 24px;
}
form :global(input) {
  width: 416px;
}
:global(button) {
  white-space: nowrap;
}
</style>
