<script>
  import { onMount } from "svelte";
  import QRCode from 'qrcode';

  export let value;
  let canvas;

  onMount(() => {
    return QRCode.toCanvas(canvas, value, {
      errorCorrectionLevel: 'H',
      margin: 0,
      width: 250,
      color: {
        light: '#0000',
        dark: '#000',
      },
    });
  });
</script>

<div class="qrcode">
  <canvas bind:this={canvas}></canvas>
  <img class="logo" src="/static/D.svg" alt=logo>
</div>

<style>
.qrcode {
  position: relative;
  display: flex;
  align-items: center;
  justify-content: center;
  width: 300px;
  height: 300px;
  background: linear-gradient(119.1deg, rgba(97, 0, 255, 0.1) 18.3%, rgba(0, 163, 255, 0.1) 32.8%, rgba(255, 153, 0, 0.1) 64.24%), #FFFFFF;
  box-shadow: 10px 15px 25px rgba(209, 217, 230, 0.4);
  border-radius: 20px;
  padding: 25px;
}
.logo {
  width: 64px;
  padding: 12px 14px;
  border-radius: 12px;
  background: linear-gradient(119.1deg, rgba(97, 0, 255, 0.1) 18.3%, rgba(0, 163, 255, 0.1) 32.8%, rgba(255, 153, 0, 0.1) 64.24%), #FFFFFF;
  z-index: 1;
}
canvas {
  position: absolute;
}
</style>
