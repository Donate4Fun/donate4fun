<div class="flex-column">
  <details>
    <summary>What is Donate4.Fun?</summary>
    Donate4.Fun is a donations platform powered by Bitcoin Lightning that allows you to tip any content creator instantly and with minimal fees.
  </details>
  <details>
    <summary>One more donation service? How is it different?</summary>
    Donate4.Fun does not require content author to register or create account before start accepting donations. You can donate first and author would be able to claim his donation later - all he would need to do is verify that he own social account that has a donation.
  </details>
  <details>
    <summary>But how would he know that I've donated him?</summary>
    You would tell him =) Really, Donate4.Fun would deliver donations for authors that provided their Bitcoin or Lightning address, but if they hadn't the only way is you write a comment that mentions your donation on "donate 4 fun". Specially for this there is browser add-on feature that simplifes it. Moreover, each comment boost recomendations for author's content inside a platform.
  </details>
  <details>
    <summary>Why Donate4.Fun instead of YouTube Membership/Patreon/etc.? </summary>
    <ul>
      <li>Pay any amount you want</li>
      <li>Single click donations</li>
      <li>All donation amount goes to an author, no service fees except few sats for Ligtning Network.</li>
    </ul>
  </details>
  <details>
    <summary>
      Why do not donate directly to a provided author's crypto-wallet or lightning address?
    </summary>
    Although it's more straighforward to pay directly to the author instead of using third-party service like Donate4.Fun, not all authors provide crypto wallet addresses, even less of them have Lightning address. For on-chain addresses it's much harder to send a donation than just click a button in Donate4.Fun extension. Anyway, we are planning to implement sending of donations directly to the author if he provided on-chain of off-chain address.
  </details>
  <details>
    <summary>How will I know that author got my donations?</summary>
    You could check author's page on a <a href="https://donate4.fun">website</a>.
  </details>
  <details>
    <summary>What if author decided not to take donations?
    In case of author didn't verify his account or didn't logged in for 6 months you will be able to revert your donation and withdraw your money back.
  </details>
  <details>
    <summary>Why should I trust Donate4.Fun?</summary>
    Our service is fully <a href="https://github.com/Donate4Fun/doante4fun" target=_blank>open source</a> and you could ensure that it works by donating to yourself:
    <ul>
      <li>donate to your YouTube channel</li>
      <li>Verify channel ownership</li>
      <li>Withdraw your funds</li>
    </ul>
    Moreover, Donate4.Fun creators do not hide their identities - you could check our social accounts in Team section.
  </details>
  <details>
    <summary>
      How to use it from a mobile device?
    </summary>
    <p>
      Mobile app is planned. Currently only desktop browsers are supported.
    </p>
  </details>
  <details>
    <summary>
      Where to get satoshis?
    </summary>
    <ul>
      <li><a target=_blank href="https://robosats.com">Exchange on Robosats</a></li>
      <li><a target=_blank href="https://thndr.games">Play THNDR.games</a></li>
      <li><a target=_blank href="https://stacker.new">Post on stacker news</a></li>
      <li><a target=_blank href="https://sats4likes.com">Like and retweet on Sats4Likes</a></li>
    </ul>
  </details>
</div>

<style>
summary {
  display: flex;
  gap: 20px;
  align-items: center;
  font-weight: 600;
  font-size: 14px;
  line-height: 22px;
  cursor: pointer;
}
summary::before {
  background-image: url("/static/plus.svg");
  content: "";
  width: 34px;
  height: 34px;
  display: block;
  transition: transform 0.3s;
  flex-shrink: 0;
}
summary::marker {
  content: "";
}
@media (max-width: 640px) {
  details:not([open]) {
    height: 88px;
  }
}
@media (min-width: 641px) {
  details:not([open]) {
    height: 72px;
  }
}
details[open] summary::before {
  transform: rotate(45deg);
}
details > *:not(summary) {
  padding-left: 54px;
  margin-bottom: 22px;
  margin-top: 22px;
  font-weight: 400;
  font-size: 14px;
  line-height: 20px;
  letter-spacing: 0.01em;
}
</style>
