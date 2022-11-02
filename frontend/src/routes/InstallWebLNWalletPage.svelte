<script>
  import Section from "$lib/Section.svelte";
  import Wallets from "$lib/Wallets.svelte";
</script>

<Section>
  <div>
    <h1>Install a WebLN enabled wallet</h1>
    <Wallets mobile={false} />
  </div>
</Section>

<style>
div {
  padding: 60px 80px;
  width: 640px;
  display: flex;
  flex-direction: column;
  gap: 40px;
}
h1 {
  align-self: center;
}
</style>
