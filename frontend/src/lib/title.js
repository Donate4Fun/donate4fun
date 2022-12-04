import { writable } from 'svelte/store';

function createTitle() {
	const {subscribe, set, update} = writable('');
	
	return {
		subscribe,
		set: (value) => {
			set(`${value} • Donate4.Fun`);
		},
		clear: () => {
			set('Donate to anyone on YouTube and Twitter with Bitcoin Lightning • Donate4.Fun');
		}
	}
}

const title = createTitle();
export default title;
