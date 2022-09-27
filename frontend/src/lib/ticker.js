import axios from "axios";
import { readable } from 'svelte/store';
import { storage } from "$lib/storage";

const updateEvery = 10 * 60 * 1000; // 10 minutes

export const btcUsdRate = readable(null, function start(set) {
	let lastUpdatedAt = storage.tickerLastUpdatedAt || 0;
  async function update() {
		if (lastUpdatedAt)
			set(storage.tickerValue);
		if (new Date() - lastUpdatedAt > updateEvery) {
			const resp = await axios.get("https://api.alternative.me/v2/ticker/bitcoin/");
			const value = resp.data.data["1"].quotes.USD.price / 100000000;
			set(value);
			storage.tickerLastUpdatedAt = lastUpdatedAt = +(new Date());
			storage.tickerValue = value;
		}
  }

	const interval = setInterval(update, updateEvery);
	update();

	return function stop() {
		clearInterval(interval);
	};
});
