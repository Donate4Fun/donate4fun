<script>
  export let amount;
</script>

<span {...$$restProps}>
  <span class="amount">{amount.toLocaleString('ru')}</span> sat
</span>

<style>
span {
  color: #19B400;
}
.amount {
  font-weight: 700;
}
</style>
