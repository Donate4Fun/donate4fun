<script>
  import { Link } from "svelte-navigator";
  import logo from '../assets/svelte.png';
</script>

<!-- img src={logo} alt="Donate4.Fun Logo" / -->
<Link to="/" style="text-decoration: none;">
  <div class="parent">
    <img class=bolt src="/static/ln-icon.svg" alt="bolt">
    <img class=text src="/static/D.svg" alt="D">
    <div class=text>
      <span class="stroke"><span>Donate4Fun</span></span>
      <span class="gradient"><span>Donate4Fun</span></span>
    </div>
  </div>
</Link>

<style>
:root {
  --stroke-width: 0.1em;
  --stroke-color: #2E6CFF;
}
@media only screen and (max-width: 640px) {
  img.bolt,div.text {
    display: None;
  }
  .stroke:after {
    content: 'D';
  }
  .gradient:after {
    content: 'D';
  }
}
@media (min-width: 641px) {
  img.text {
    display: none;
  }
}
div.parent {
  display: flex;
  gap: 0.5em;
}
div.text {
  font-weight: 900;
  font-size: 32px;
  line-height: 39px;
}
span.gradient {
  background: linear-gradient(90deg, #F9F03E 0%, #9DEDA2 100%), linear-gradient(299.9deg, #FF7A00 18.72%, #FFA800 82.21%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
  text-fill-color: transparent;
}
span.stroke {
  position: absolute;
  z-index: -1;
  text-shadow:
    0                               var(--stroke-width)             var(--stroke-color),
    0                               calc(-1 * var(--stroke-width))  var(--stroke-color),
    calc(-1 * var(--stroke-width))  0                               var(--stroke-color),
    var(--stroke-width)             0                               var(--stroke-color),
    calc(1 * var(--stroke-width))  calc(1 * var(--stroke-width))  var(--stroke-color),
    calc(-1 * var(--stroke-width)) calc(1 * var(--stroke-width))  var(--stroke-color),
    calc(1 * var(--stroke-width))  calc(-1 * var(--stroke-width)) var(--stroke-color),
    calc(-1 * var(--stroke-width)) calc(-1 * var(--stroke-width)) var(--stroke-color);
}
</style>
