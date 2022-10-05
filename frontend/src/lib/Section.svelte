<section class={$$restProps.class}>
  <slot />
</section>
<style>
section {
  background: #FFFFFF;
  border: 1px solid rgba(26, 41, 82, 0.05);
  border-radius: 20px;
  box-shadow: 10px 15px 20px rgba(209, 217, 230, 0.15);

  font-size: 18px;
  line-height: 24px;

  /* identical to box height, or 133% */
  letter-spacing: 0.015em;

  padding: var(--padding);
  width: var(--width, fit-content);  /* replace with 100% always */
  height: var(--height, fit-content);
}
</style>
