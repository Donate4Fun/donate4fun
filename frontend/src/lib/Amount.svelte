<script>
  export let amount;
</script>

<span class="container">
  <span class="amount">{amount.toLocaleString('ru')}</span> sats
</span>

<style>
.container {
  color: #19B400;
  white-space: nowrap;
}
.amount {
  font-weight: 700;
}
</style>
