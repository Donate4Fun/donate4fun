<script>
  import Header from "../lib/Header.svelte";
  import Footer from "../lib/Footer.svelte";
</script>

<div class="container">
  <div class="item">
    <Header />
    <slot />
  </div>
</div>
<Footer />

<style>
.container {
  display: flex;
  flex-direction: column;
  align-items: center;
}
.item {
  display: flex;
  flex-direction: column;
}

</style>
