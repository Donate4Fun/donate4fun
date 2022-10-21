<script>
  export let open;
</script>

<div class="root" class:no-plus={open}>
  <details {open}>
    <summary>What is Donate4.Fun?</summary>
    <div>
      Donate4.Fun is a donations platform powered by Bitcoin Lightning that allows you to tip any content creator instantly and with minimal fees.
    </div>
  </details>
  <details {open}>
    <summary>One more donation service? How is it different?</summary>
    <div>
      Donate4.Fun does not require content authors to register or create an account to start accepting donations.
      You can donate first and the author would be able to claim his donation later - all he would need to do is verify that he owns a social account that has a donation
    </div>
  </details>
  <details {open}>
    <summary>But how would author know about the donation?</summary>
    <div>
      You should tell it =) Really, Donate4.Fun would deliver donations for authors that provided their Bitcoin or Lightning address, but if they hadn't the only way is you write a comment that mentions your donation on "donate 4 fun".
      Specially for this there is a browser add-on feature that simplifies it. Moreover, each comment boosts recommendations for the author's content inside a platform.
    </div>
  </details>
  <details {open}>
    <summary>Why Donate4.Fun instead of YouTube Membership/Patreon/etc.? </summary>
    <ul>
      <li>Pay any amount you want</li>
      <li>Single click donations</li>
      <li>All donation amount goes to an author, no service fees except few sats for Ligtning Network.</li>
    </ul>
  </details>
  <details {open}>
    <summary>
      Why do not donate directly to a provided author's crypto-wallet or lightning address?
    </summary>
    <div>
      Although it's more straightforward to pay directly to the author instead of using a third-party service like Donate4.Fun, not all authors provide crypto wallet addresses, even less of them have Lightning addresses.
      For on-chain addresses it's much harder to send a donation than just click a button in Donate4.Fun extension.
      Anyway, we are planning to implement sending of donations directly to the author if he provided an on-chain or off-chain address.
    </div>
  </details>
  <details {open}>
    <summary>How will I know that author got my donations?</summary>
    <div>
      You could check the author's page on a <a href="https://donate4.fun">website</a>.
    </div>
  </details>
  <details {open}>
    <summary>What if author decided not to take donations?</summary>
    <div>
      In case when the author didn't verify his account or didn't log in for 6 months you will be able to revert your donation and withdraw your money back.
    </div>
  </details>
  <details {open}>
    <summary>Why should I trust Donate4.Fun?</summary>
    <div>
      Our service is fully <a href="https://github.com/Donate4Fun/doante4fun" target=_blank>open source</a> and you could ensure that it works by donating to yourself:
      <ul>
        <li>donate to your YouTube channel</li>
        <li>Verify channel ownership</li>
        <li>Withdraw your funds</li>
      </ul>
      Moreover, Donate4.Fun creators do not hide their identities - you could check our social accounts in Team section.
    </div>
  </details>
  <details {open}>
    <summary>How to use it from a mobile device?</summary>
    <div>
      Mobile app is planned. Currently only desktop browsers are supported.
    </div>
  </details>
  <details {open}>
    <summary>Where to get satoshis?</summary>
    <ul>
      <li><a target=_blank href="https://robosats.com">Exchange on Robosats</a></li>
      <li><a target=_blank href="https://thndr.games">Play THNDR.games</a></li>
      <li><a target=_blank href="https://stacker.new">Post on stacker news</a></li>
      <li><a target=_blank href="https://sats4likes.com">Like and retweet on Sats4Likes</a></li>
    </ul>
  </details>
</div>

<style>
.root {
  display: flex;
  flex-direction: column;
  --padding: 40px;
}
summary {
  display: flex;
  gap: 20px;
  align-items: center;
  font-weight: 600;
  font-size: 16px;
  line-height: 24px;
  cursor: pointer;
  padding: 0 var(--padding);
  height: 88px;
}
summary:hover {
  background: rgba(157, 237, 162, 0.1);
}
summary::before {
  background-image: url("/static/plus.svg");
  background-repeat: no-repeat;
  background-position-y: center;
  content: "";
  width: 34px;
  height: 34px;
  display: block;
  transition: transform 0.3s;
  flex-shrink: 0;
}
.no-plus summary::before {
  display: none;
}
.no-plus summary {
  pointer-events: none;
}
summary::marker {
  content: "";
}
details[open] summary::before {
  transform: rotate(45deg);
}
details > *:not(summary) {
  padding: 0 var(--padding);
  font-weight: 400;
  font-size: 16px;
  line-height: 24px;
  letter-spacing: 0.01em;
  transition: transform 0.3s;
  transform: scaleY(0);
  transform-origin: top;
}
details > ul {
  padding-left: calc(var(--padding) + 15px);
  padding-right: var(--padding);
}
details[open] > *:not(summary) {
  transform: scaleY(1);
  padding-bottom: 48px;
}
</style>
