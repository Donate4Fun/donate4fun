<div {...$$restProps}></div>

<style>
div {
  ---size: var(--size, 1em);
  ---color: var(--color, black);
  ---width: var(--width, 4px);

  width: var(---size);
  height: var(---size);
  animation: spin 1.5s infinite linear;
  aspect-ratio: 1;
  position: relative;
  z-index: 0;
  display: inline-block;
}

div:after {
  content: '';
  width: var(---width);
  height: var(---width);
  border-radius: 50%;
  background: var(---color);
  position: absolute;
  left: 0;
  bottom: calc((var(---size) - var(---width)) / 2);
}

div:before {
  content: "";
  position: absolute;
  z-index: -1;
  inset: 0;
  background: conic-gradient(transparent, var(---color) 270deg, transparent 270deg, transparent 360deg);
  padding: var(---width);
  border-radius: 50%;
  mask:
     linear-gradient(#fff 0 0) content-box,
     linear-gradient(#fff 0 0);
  mask-composite: exclude !important;
  -webkit-mask:
     linear-gradient(#fff 0 0) content-box,
     linear-gradient(#fff 0 0);
  -webkit-mask-composite: clear;
}

@keyframes spin {
  100% {
    transform: rotate(360deg);
  }
}
</style>
