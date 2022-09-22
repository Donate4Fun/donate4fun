<script>
  export let number;
</script>


<div class="flex-row gap-12 align-center">
  <div class="number">{number}</div>
  <slot />
</div>

<style>
.number {
  width: 40px;
  height: 40px;
  background: linear-gradient(90deg, rgba(249, 240, 62, 0.15) 0%, rgba(157, 237, 162, 0.15) 100%), #FFFFFF;
  border: 1px solid rgba(26, 41, 82, 0.05);
  border-radius: 20px;

  font-weight: 900;
  font-size: 20px;
  line-height: 18px;

  text-align: center;
}
</style>
