<script>
  import Header from "$lib/Header.svelte";
  import Footer from "$lib/Footer.svelte";
  import Toast from "$lib/Toast.svelte";
  import Consent from "$lib/Consent.svelte";
</script>

<div class="page">
  <Header />
  <Toast />
  <div class="content">
    <slot />
  </div>
  <Footer />
  <Consent />
</div>

<style>
.page {
  display: flex;
  flex-direction: column;
  align-items: center;
  min-height: 100vh;
  background-color: var(--background-color);
  background-image: url("/static/background-bolt.svg");
  background-repeat: no-repeat;
  background-position: top;
}
.content {
  flex: 1;
  padding-top: 64px;
}
@media (max-width: 640px) {
  .content {
    padding-top: 0;
    width: 100vw;
  }
}
</style>
