<section class="flex-grow-1">
  <div class="inner flex-column">
    <slot />
  </div>
</section>

<style>
section {
  background-image: linear-gradient(to right, #F9F03E 0%, #9DEDA2 100%);
  --border-radius: 20px;
  --border-width: 2px;
  border-top-left-radius: var(--border-radius);
  border-top-right-radius: var(--border-radius);
  padding: var(--border-width);
  height: 100%;
  max-height: 360px;
}
section > div {
  width: 100%;
  height: 100%;
  background: white;
  border-top-left-radius: calc(var(--border-radius) - var(--border-width));
  border-top-right-radius: calc(var(--border-radius) - var(--border-width));
  padding: 32px;
  align-items: var(--align-items);
  justify-content: var(--justify-content);
}
</style>
