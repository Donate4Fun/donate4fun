<script>
  import Section from "$lib/Section.svelte";
  import FAQ from "$lib/FAQ.svelte";
</script>

<Section>
  <div>
    <h1>FAQ</h1>
    <FAQ open />
  </div>
</Section>

<style>
div {
  max-width: 560px
}
h1 {
  padding: 40px 40px 20px;
  font-family: 'Montserrat';
  font-weight: 900;
  font-size: 40px;
  line-height: 56px;

  /* identical to box height, or 140% */

  background: linear-gradient(90deg, #FF4B4B 0%, #DC24A9 100%), #FFF;
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
  text-fill-color: transparent;
}
</style>
