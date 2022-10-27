<script>
  import { Confetti } from "svelte-confetti";
  import LandingSteps from "$lib/LandingSteps.svelte";
</script>

<div style="
  position: fixed;
  top: -50px;
  left: 0;
  height: 100vh;
  width: 100vw;
  display: flex;
  justify-content: center;
  overflow: hidden;
  pointer-events: none;"
>
  <Confetti x={[-4, 4]} y={[-0.2, 0.1]} delay={[0, 2000]} duration=5000 amount=200 fallDistance="100vh" />
</div>
<main>
  <h1>Thank you for downloading Donate4.Fun</h1>
  <p class="annotation">👇Complete the setup👇</p>
  <LandingSteps />
</main>

<style>
main {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 16px;
}
h1 {
  font-family: 'Montserrat';
  font-weight: 900;
  font-size: 32px;
  line-height: 56px;
  background: linear-gradient(89.59deg, #FF9634 27.11%, #DC24A9 92.47%), #FFF;
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
  text-fill-color: transparent;
}
p {
  font-weight: 500;
  font-size: 20px;
  line-height: 30px;
  margin-bottom: 24px;
}
</style>
