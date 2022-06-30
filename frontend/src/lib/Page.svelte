<script>
  import Header from "../lib/Header.svelte";
  import Footer from "../lib/Footer.svelte";
</script>

<div class="container">
  <div class="item">
    <Header class="page-header" />
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
  align-items: center;
  width: 1280px;
}
@media only screen and (max-width: 1280px) {
  .item {
    width: 100%;
  }
}
:global(.page-header) {
  margin-bottom: 16px;
}
</style>
