<script>
  export let number;
</script>

<div class="number-circle flex-row align-center justify-center">
  <div class="number-digit">{number}</div>
</div>

<style>
.number-circle {
  flex-shrink: 0;
  width: var(--size, 40px);
  height: var(--size, 40px);
  background: linear-gradient(90deg, rgba(249, 240, 62, 0.15) 0%, rgba(157, 237, 162, 0.15) 100%), #FFFFFF;
  border: 1px solid rgba(26, 41, 82, 0.05);
  border-radius: 100%;
  box-shadow: 10px 15px 25px rgba(209, 217, 230, 0.4);

  font-weight: 900;
  font-size: 20px;
  line-height: 18px;
}
.number-digit {
  background: radial-gradient(74.17% 74.17% at 65% 25.83%, rgba(255, 220, 220, 0.58) 0%, rgba(254, 207, 207, 0) 100%) /* warning: gradient uses a rotation that is not supported by CSS and may not behave as expected */, #2E6CFF;
  background-clip: text;
  text-fill-color: transparent;
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
}
</style>
