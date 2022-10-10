<script>
  import { LottiePlayer } from '@lottiefiles/svelte-lottie-player';
  import { getStatic } from './common.js';
</script>
<LottiePlayer
  src={getStatic("lottie-arrow.json")}
  autoplay={true}
  loop={true}
  width={30}
  background=transparent
  controls={null}
  controlsLayout={[]}
  height={null}
/>
