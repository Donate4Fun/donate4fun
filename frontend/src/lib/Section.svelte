<section class={$$props.class}>
  <slot />
</section>
<style>
section {
  padding: 40px;
  margin: 0px;

  background: #FFFFFF;
  border: 1px solid rgba(26, 41, 82, 0.05);
  border-radius: 20px;

  font-size: 18px;
  line-height: 24px;

  /* identical to box height, or 133% */
  letter-spacing: 0.015em;
}
section :global(h1) {
  font-weight: 700;
  font-size: 24px;
  line-height: 29px;
  margin: 0 0;
}
h1, p {
  margin: inherit;
}
</style>
