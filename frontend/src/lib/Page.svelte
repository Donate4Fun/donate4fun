<script>
  import Header from "../lib/Header.svelte";
  import Footer from "../lib/Footer.svelte";
  import Toast from "../lib/Toast.svelte";
</script>

<div class="page">
  <Header />
  <Toast />
  <div class="content">
    <slot />
  </div>
  <Footer />
</div>

<style>
.page {
  display: flex;
  flex-direction: column;
  align-items: center;
  min-height: 100vh;
  background-color: #F7F9FF;
}
.content {
  flex: 1;
}
</style>
