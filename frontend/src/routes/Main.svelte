<script>
  import Donate from '$lib/Donate.svelte';
  import Claim from '../lib/Claim.svelte';
  import LatestDonations from "../lib/LatestDonations.svelte";
  import Header from "../lib/Header.svelte";
  import Extensions from "../lib/Extensions.svelte";
  import Footer from "../lib/Footer.svelte";
  import Section from "../lib/Section.svelte";
  import title from "../lib/title.js";

  const showInstruction = false;

  title.clear();
</script>

<header>
  <h1>Donate anyone on YouTube</h1>
  Instant delivery with Lightning network. No KYC. Any amount.
</header>
{#if showInstruction}
<ol>
  <li>
    <Extensions />
  </li>
  <li>
    <div class="flex-column font-large">
      Bolt icon will appear under YouTube videos
      <img alt="instruction-youtube-button" src="/static/instruction-youtube-button.png">
      Click on it to give a tip to the author for this video
    </div>
  </li>
  <li>
    <div class="flex-column font-large">
      Post a comment to give author a hint how to take your tip.
      <img alt="instruction-youtube-comment" src="/static/instruction-youtube-comment.png">
    </div>
  </li>
</ol>
{/if}
<main>
  <div class="forms">
    <Donate />
    <Claim />
  </div>
  <LatestDonations />
</main>
<article>
  <div class="how-title">How it works</div>
  <ul>
    <li>Copy and paste YouTube video or channel URL to the form</li>
    <li>Donate to YouTuber any amount using your BTC Lightning Wallet</li>
    <li>Send YouTuber a comment with the link</li>
    <li>YouTuber follows the link, authorizes using YouTube and withdraws his money to his Lightning Wallet</li>
  </ul>
</article>

<style>
h1 {
  font-weight: 900;
  font-size: 44px;
  line-height: 53px;
  margin-bottom: 20px;
}
@media only screen and (max-width: 1280px) {
  main {
    flex-direction: column;
  }
}
@media only screen and (max-width: 640px) {
  main,article,header {
    padding-left: 24px;
    padding-right: 24px;
  }
  header {
    text-align: center;
  }
}
header {
  font-size: 24px;
  line-height: 29px;
  padding-left: 40px;
  padding-right: 40px;
  align-self: start;
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
article {
  align-self: center;
  margin-top: 92px;
}
.how-title {
  font-size: 24px;
  font-weight: 700;
  text-align: center;
}
ul {
  box-sizing: border-box;
}
img {
  height: auto;
  width: auto;
  max-width: 400px;
  max-height: 300px;
}
</style>
