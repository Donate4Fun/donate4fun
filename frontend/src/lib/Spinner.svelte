<script>
  export let width = '4px';
  export let color = 'black';
  export let size = '1em';
</script>


<div style="--width:{width}; --color:{color}; --size:{size}"></div>

<style>
:root {
  --width: 4px;
  --color: white;
  --size: 28px;
}

div {
  width: var(--size);
  height: var(--size);
  animation: spin 1.5s infinite linear;
  margin: 0 auto;
  aspect-ratio: 1;
  position: relative;
  z-index: 0;
  display: inline-block;
}

div:after {
  content: '';
  width: var(--width);
  height: var(--width);
  border-radius: 50%;
  background: var(--color);
  position: absolute;
  left: 0;
  bottom: calc((var(--size) - var(--width)) / 2);
}

div:before {
  content: "";
  position: absolute;
  z-index: -1;
  inset: 0;
  background: conic-gradient(transparent, var(--color) 270deg, transparent 270deg, transparent 360deg);
  padding: var(--width);
  border-radius: 50%;
  mask:
     linear-gradient(#fff 0 0) content-box,
     linear-gradient(#fff 0 0);
  mask-composite: exclude;
}

@keyframes spin {
  100% {
    transform: rotate(360deg);
  }
}
</style>
