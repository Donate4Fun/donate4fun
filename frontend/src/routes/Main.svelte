<script>
  import Donate from '../lib/Donate.svelte';
  import Claim from '../lib/Claim.svelte';
  import LatestDonations from "../lib/LatestDonations.svelte";
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
    <div class="forms">
      <Donate />
      <Claim />
    </div>
    <div class="latest">
      <LatestDonations />
    </div>
  </main>
  <article>
    How to use this service:
  </article>
</article>
<Footer />

<style>
@media only screen and (max-width: 1200px) {
  .latest {
    display: none;
  }
}
main {
  display: flex;
  gap: 20px;
  padding-top: 40px;
}
.forms {
  display: flex;
  flex-direction: column;
  gap: 20px;
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
