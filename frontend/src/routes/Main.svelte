<script>
  import Donate from '../lib/Donate.svelte';
  import Claim from '../lib/Claim.svelte';
  import Donations from "../lib/Donations.svelte";
  import Header from "../lib/Header.svelte";
  import Footer from "../lib/Footer.svelte";
</script>

<Header />
<article>
  <header>
    <h1>Donate your favorite blogger</h1>
    Instant delivery with Lightning network. No KYC.
  </header>
  <main>
    <section class="forms">
      <Donate />
      <Claim />
      <article>
        FAQ
      </article>
    </section>
    <aside>
      <Donations />
    </aside>
  </main>
</article>
<Footer />

<style>
  main {
    display: flex;
    flex-grow: 1;
    gap: 20px;
    padding-top: 40px;
  }
  .forms {
    display: flex;
    flex-direction: column;
    flex-basis: 60%;
    gap: 20px;
  }
  aside {
    flex-basis: 40%;
  }
  header {
    font-size: 24px;
    line-height: 29px;
  }
  h1 {
    font-weight: 900;
    font-size: 44px;
    line-height: 53px;
  }
</style>
