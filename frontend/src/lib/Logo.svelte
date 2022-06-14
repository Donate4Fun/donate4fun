<script>
  import { Link } from "svelte-navigator";
  import logo from '../assets/svelte.png';
</script>

<!-- img src={logo} alt="Donate4.Fun Logo" / -->
<Link to="/" style="text-decoration: none;"><div class="parent"><img src="/ln-icon.svg" alt="bolt"><div class="text"><span class="stroke">Donate4Fun</span><span class="gradient">Donate4Fun</span><sup>BETA</sup></div></div></Link>

<style>
:root {
  --stroke-width: 0.1em;
  --stroke-color: #2E6CFF;
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
div sup {
  font-size: 14px;
  line-height: 19px;
  font-weight: 700;
  color: var(--stroke-color);
  position: relative;
  top: -0.7em;
}
</style>
