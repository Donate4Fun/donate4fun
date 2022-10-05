<div class="flex-column">
  <details>
    <summary>
      Why Donate4.Fun instead of YouTube Membership/Patreon/etc.? 
    </summary>
    <ul>
      <li>Pay any amount you want</li>
      <li>Single click donations</li>
      <li>All donation amount goes to an author, no service fees except few sats for Ligtning Network.</li>
    </ul>
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
details:not([open]) {
  height: 72px;
}
details[open] summary::before {
  transform: rotate(45deg);
}
details > *:not(summary) {
  padding-left: 54px;
  font-size: 12px;
  margin-bottom: 22px;
  margin-top: 22px;
}
</style>
