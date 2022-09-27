<section class="flex-grow-1">
  <div class="inner flex-column">
    <slot />
  </div>
</section>

<style>
section {
  background-image: linear-gradient(to right, #F9F03E 0%, #9DEDA2 100%);
  border-radius: 20px;
  padding: 2px;
  height: 100%;
}
section > div {
  width: 100%;
  height: 100%;
  background: white;
  border-radius: 20px;
  padding: 40px 32px 36px 32px;
  align-items: var(--align-items);
  justify-content: var(--justify-content);
}
</style>
