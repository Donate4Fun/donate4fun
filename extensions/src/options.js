var app = (function () {
    'use strict';

    function noop() { }
    function assign(tar, src) {
        // @ts-ignore
        for (const k in src)
            tar[k] = src[k];
        return tar;
    }
    function is_promise(value) {
        return value && typeof value === 'object' && typeof value.then === 'function';
    }
    function run(fn) {
        return fn();
    }
    function blank_object() {
        return Object.create(null);
    }
    function run_all(fns) {
        fns.forEach(run);
    }
    function is_function(thing) {
        return typeof thing === 'function';
    }
    function safe_not_equal(a, b) {
        return a != a ? b == b : a !== b || ((a && typeof a === 'object') || typeof a === 'function');
    }
    function is_empty(obj) {
        return Object.keys(obj).length === 0;
    }
    function exclude_internal_props(props) {
        const result = {};
        for (const k in props)
            if (k[0] !== '$')
                result[k] = props[k];
        return result;
    }
    function compute_rest_props(props, keys) {
        const rest = {};
        keys = new Set(keys);
        for (const k in props)
            if (!keys.has(k) && k[0] !== '$')
                rest[k] = props[k];
        return rest;
    }
    function append(target, node) {
        target.appendChild(node);
    }
    function insert(target, node, anchor) {
        target.insertBefore(node, anchor || null);
    }
    function detach(node) {
        node.parentNode.removeChild(node);
    }
    function destroy_each(iterations, detaching) {
        for (let i = 0; i < iterations.length; i += 1) {
            if (iterations[i])
                iterations[i].d(detaching);
        }
    }
    function element(name) {
        return document.createElement(name);
    }
    function text(data) {
        return document.createTextNode(data);
    }
    function space() {
        return text(' ');
    }
    function empty() {
        return text('');
    }
    function listen(node, event, handler, options) {
        node.addEventListener(event, handler, options);
        return () => node.removeEventListener(event, handler, options);
    }
    function attr(node, attribute, value) {
        if (value == null)
            node.removeAttribute(attribute);
        else if (node.getAttribute(attribute) !== value)
            node.setAttribute(attribute, value);
    }
    function set_attributes(node, attributes) {
        // @ts-ignore
        const descriptors = Object.getOwnPropertyDescriptors(node.__proto__);
        for (const key in attributes) {
            if (attributes[key] == null) {
                node.removeAttribute(key);
            }
            else if (key === 'style') {
                node.style.cssText = attributes[key];
            }
            else if (key === '__value') {
                node.value = node[key] = attributes[key];
            }
            else if (descriptors[key] && descriptors[key].set) {
                node[key] = attributes[key];
            }
            else {
                attr(node, key, attributes[key]);
            }
        }
    }
    function children(element) {
        return Array.from(element.childNodes);
    }
    function set_data(text, data) {
        data = '' + data;
        if (text.wholeText !== data)
            text.data = data;
    }
    function set_input_value(input, value) {
        input.value = value == null ? '' : value;
    }
    function set_style(node, key, value, important) {
        if (value === null) {
            node.style.removeProperty(key);
        }
        else {
            node.style.setProperty(key, value, important ? 'important' : '');
        }
    }
    function toggle_class(element, name, toggle) {
        element.classList[toggle ? 'add' : 'remove'](name);
    }
    function custom_event(type, detail, { bubbles = false, cancelable = false } = {}) {
        const e = document.createEvent('CustomEvent');
        e.initCustomEvent(type, bubbles, cancelable, detail);
        return e;
    }

    let current_component;
    function set_current_component(component) {
        current_component = component;
    }
    function get_current_component() {
        if (!current_component)
            throw new Error('Function called outside component initialization');
        return current_component;
    }
    function createEventDispatcher() {
        const component = get_current_component();
        return (type, detail, { cancelable = false } = {}) => {
            const callbacks = component.$$.callbacks[type];
            if (callbacks) {
                // TODO are there situations where events could be dispatched
                // in a server (non-DOM) environment?
                const event = custom_event(type, detail, { cancelable });
                callbacks.slice().forEach(fn => {
                    fn.call(component, event);
                });
                return !event.defaultPrevented;
            }
            return true;
        };
    }
    // TODO figure out if we still want to support
    // shorthand events, or if we want to implement
    // a real bubbling mechanism
    function bubble(component, event) {
        const callbacks = component.$$.callbacks[event.type];
        if (callbacks) {
            // @ts-ignore
            callbacks.slice().forEach(fn => fn.call(this, event));
        }
    }

    const dirty_components = [];
    const binding_callbacks = [];
    const render_callbacks = [];
    const flush_callbacks = [];
    const resolved_promise = Promise.resolve();
    let update_scheduled = false;
    function schedule_update() {
        if (!update_scheduled) {
            update_scheduled = true;
            resolved_promise.then(flush);
        }
    }
    function add_render_callback(fn) {
        render_callbacks.push(fn);
    }
    function add_flush_callback(fn) {
        flush_callbacks.push(fn);
    }
    // flush() calls callbacks in this order:
    // 1. All beforeUpdate callbacks, in order: parents before children
    // 2. All bind:this callbacks, in reverse order: children before parents.
    // 3. All afterUpdate callbacks, in order: parents before children. EXCEPT
    //    for afterUpdates called during the initial onMount, which are called in
    //    reverse order: children before parents.
    // Since callbacks might update component values, which could trigger another
    // call to flush(), the following steps guard against this:
    // 1. During beforeUpdate, any updated components will be added to the
    //    dirty_components array and will cause a reentrant call to flush(). Because
    //    the flush index is kept outside the function, the reentrant call will pick
    //    up where the earlier call left off and go through all dirty components. The
    //    current_component value is saved and restored so that the reentrant call will
    //    not interfere with the "parent" flush() call.
    // 2. bind:this callbacks cannot trigger new flush() calls.
    // 3. During afterUpdate, any updated components will NOT have their afterUpdate
    //    callback called a second time; the seen_callbacks set, outside the flush()
    //    function, guarantees this behavior.
    const seen_callbacks = new Set();
    let flushidx = 0; // Do *not* move this inside the flush() function
    function flush() {
        const saved_component = current_component;
        do {
            // first, call beforeUpdate functions
            // and update components
            while (flushidx < dirty_components.length) {
                const component = dirty_components[flushidx];
                flushidx++;
                set_current_component(component);
                update(component.$$);
            }
            set_current_component(null);
            dirty_components.length = 0;
            flushidx = 0;
            while (binding_callbacks.length)
                binding_callbacks.pop()();
            // then, once components are updated, call
            // afterUpdate functions. This may cause
            // subsequent updates...
            for (let i = 0; i < render_callbacks.length; i += 1) {
                const callback = render_callbacks[i];
                if (!seen_callbacks.has(callback)) {
                    // ...so guard against infinite loops
                    seen_callbacks.add(callback);
                    callback();
                }
            }
            render_callbacks.length = 0;
        } while (dirty_components.length);
        while (flush_callbacks.length) {
            flush_callbacks.pop()();
        }
        update_scheduled = false;
        seen_callbacks.clear();
        set_current_component(saved_component);
    }
    function update($$) {
        if ($$.fragment !== null) {
            $$.update();
            run_all($$.before_update);
            const dirty = $$.dirty;
            $$.dirty = [-1];
            $$.fragment && $$.fragment.p($$.ctx, dirty);
            $$.after_update.forEach(add_render_callback);
        }
    }
    const outroing = new Set();
    let outros;
    function group_outros() {
        outros = {
            r: 0,
            c: [],
            p: outros // parent group
        };
    }
    function check_outros() {
        if (!outros.r) {
            run_all(outros.c);
        }
        outros = outros.p;
    }
    function transition_in(block, local) {
        if (block && block.i) {
            outroing.delete(block);
            block.i(local);
        }
    }
    function transition_out(block, local, detach, callback) {
        if (block && block.o) {
            if (outroing.has(block))
                return;
            outroing.add(block);
            outros.c.push(() => {
                outroing.delete(block);
                if (callback) {
                    if (detach)
                        block.d(1);
                    callback();
                }
            });
            block.o(local);
        }
        else if (callback) {
            callback();
        }
    }

    function handle_promise(promise, info) {
        const token = info.token = {};
        function update(type, index, key, value) {
            if (info.token !== token)
                return;
            info.resolved = value;
            let child_ctx = info.ctx;
            if (key !== undefined) {
                child_ctx = child_ctx.slice();
                child_ctx[key] = value;
            }
            const block = type && (info.current = type)(child_ctx);
            let needs_flush = false;
            if (info.block) {
                if (info.blocks) {
                    info.blocks.forEach((block, i) => {
                        if (i !== index && block) {
                            group_outros();
                            transition_out(block, 1, 1, () => {
                                if (info.blocks[i] === block) {
                                    info.blocks[i] = null;
                                }
                            });
                            check_outros();
                        }
                    });
                }
                else {
                    info.block.d(1);
                }
                block.c();
                transition_in(block, 1);
                block.m(info.mount(), info.anchor);
                needs_flush = true;
            }
            info.block = block;
            if (info.blocks)
                info.blocks[index] = block;
            if (needs_flush) {
                flush();
            }
        }
        if (is_promise(promise)) {
            const current_component = get_current_component();
            promise.then(value => {
                set_current_component(current_component);
                update(info.then, 1, info.value, value);
                set_current_component(null);
            }, error => {
                set_current_component(current_component);
                update(info.catch, 2, info.error, error);
                set_current_component(null);
                if (!info.hasCatch) {
                    throw error;
                }
            });
            // if we previously had a then/catch block, destroy it
            if (info.current !== info.pending) {
                update(info.pending, 0);
                return true;
            }
        }
        else {
            if (info.current !== info.then) {
                update(info.then, 1, info.value, promise);
                return true;
            }
            info.resolved = promise;
        }
    }
    function update_await_block_branch(info, ctx, dirty) {
        const child_ctx = ctx.slice();
        const { resolved } = info;
        if (info.current === info.then) {
            child_ctx[info.value] = resolved;
        }
        if (info.current === info.catch) {
            child_ctx[info.error] = resolved;
        }
        info.block.p(child_ctx, dirty);
    }

    function get_spread_update(levels, updates) {
        const update = {};
        const to_null_out = {};
        const accounted_for = { $$scope: 1 };
        let i = levels.length;
        while (i--) {
            const o = levels[i];
            const n = updates[i];
            if (n) {
                for (const key in o) {
                    if (!(key in n))
                        to_null_out[key] = 1;
                }
                for (const key in n) {
                    if (!accounted_for[key]) {
                        update[key] = n[key];
                        accounted_for[key] = 1;
                    }
                }
                levels[i] = n;
            }
            else {
                for (const key in o) {
                    accounted_for[key] = 1;
                }
            }
        }
        for (const key in to_null_out) {
            if (!(key in update))
                update[key] = undefined;
        }
        return update;
    }

    function bind(component, name, callback) {
        const index = component.$$.props[name];
        if (index !== undefined) {
            component.$$.bound[index] = callback;
            callback(component.$$.ctx[index]);
        }
    }
    function create_component(block) {
        block && block.c();
    }
    function mount_component(component, target, anchor, customElement) {
        const { fragment, on_mount, on_destroy, after_update } = component.$$;
        fragment && fragment.m(target, anchor);
        if (!customElement) {
            // onMount happens before the initial afterUpdate
            add_render_callback(() => {
                const new_on_destroy = on_mount.map(run).filter(is_function);
                if (on_destroy) {
                    on_destroy.push(...new_on_destroy);
                }
                else {
                    // Edge case - component was destroyed immediately,
                    // most likely as a result of a binding initialising
                    run_all(new_on_destroy);
                }
                component.$$.on_mount = [];
            });
        }
        after_update.forEach(add_render_callback);
    }
    function destroy_component(component, detaching) {
        const $$ = component.$$;
        if ($$.fragment !== null) {
            run_all($$.on_destroy);
            $$.fragment && $$.fragment.d(detaching);
            // TODO null out other refs, including component.$$ (but need to
            // preserve final state?)
            $$.on_destroy = $$.fragment = null;
            $$.ctx = [];
        }
    }
    function make_dirty(component, i) {
        if (component.$$.dirty[0] === -1) {
            dirty_components.push(component);
            schedule_update();
            component.$$.dirty.fill(0);
        }
        component.$$.dirty[(i / 31) | 0] |= (1 << (i % 31));
    }
    function init(component, options, instance, create_fragment, not_equal, props, append_styles, dirty = [-1]) {
        const parent_component = current_component;
        set_current_component(component);
        const $$ = component.$$ = {
            fragment: null,
            ctx: null,
            // state
            props,
            update: noop,
            not_equal,
            bound: blank_object(),
            // lifecycle
            on_mount: [],
            on_destroy: [],
            on_disconnect: [],
            before_update: [],
            after_update: [],
            context: new Map(options.context || (parent_component ? parent_component.$$.context : [])),
            // everything else
            callbacks: blank_object(),
            dirty,
            skip_bound: false,
            root: options.target || parent_component.$$.root
        };
        append_styles && append_styles($$.root);
        let ready = false;
        $$.ctx = instance
            ? instance(component, options.props || {}, (i, ret, ...rest) => {
                const value = rest.length ? rest[0] : ret;
                if ($$.ctx && not_equal($$.ctx[i], $$.ctx[i] = value)) {
                    if (!$$.skip_bound && $$.bound[i])
                        $$.bound[i](value);
                    if (ready)
                        make_dirty(component, i);
                }
                return ret;
            })
            : [];
        $$.update();
        ready = true;
        run_all($$.before_update);
        // `false` as a special case of no DOM component
        $$.fragment = create_fragment ? create_fragment($$.ctx) : false;
        if (options.target) {
            if (options.hydrate) {
                const nodes = children(options.target);
                // eslint-disable-next-line @typescript-eslint/no-non-null-assertion
                $$.fragment && $$.fragment.l(nodes);
                nodes.forEach(detach);
            }
            else {
                // eslint-disable-next-line @typescript-eslint/no-non-null-assertion
                $$.fragment && $$.fragment.c();
            }
            if (options.intro)
                transition_in(component.$$.fragment);
            mount_component(component, options.target, options.anchor, options.customElement);
            flush();
        }
        set_current_component(parent_component);
    }
    /**
     * Base class for Svelte components. Used when dev=false.
     */
    class SvelteComponent {
        $destroy() {
            destroy_component(this, 1);
            this.$destroy = noop;
        }
        $on(type, callback) {
            const callbacks = (this.$$.callbacks[type] || (this.$$.callbacks[type] = []));
            callbacks.push(callback);
            return () => {
                const index = callbacks.indexOf(callback);
                if (index !== -1)
                    callbacks.splice(index, 1);
            };
        }
        $set($$props) {
            if (this.$$set && !is_empty($$props)) {
                this.$$.skip_bound = true;
                this.$$set($$props);
                this.$$.skip_bound = false;
            }
        }
    }

    /* Slider.svelte generated by Svelte v3.49.0 */

    function create_fragment$4(ctx) {
    	let label;
    	let input;
    	let t;
    	let span;
    	let mounted;
    	let dispose;

    	return {
    		c() {
    			label = element("label");
    			input = element("input");
    			t = space();
    			span = element("span");
    			attr(input, "type", "checkbox");
    			attr(input, "class", "svelte-a4i618");
    			attr(span, "class", "slider svelte-a4i618");
    			attr(label, "class", "switch svelte-a4i618");
    		},
    		m(target, anchor) {
    			insert(target, label, anchor);
    			append(label, input);
    			input.checked = /*value*/ ctx[0];
    			append(label, t);
    			append(label, span);

    			if (!mounted) {
    				dispose = [
    					listen(input, "change", /*input_change_handler*/ ctx[2]),
    					listen(input, "change", /*change_handler*/ ctx[1])
    				];

    				mounted = true;
    			}
    		},
    		p(ctx, [dirty]) {
    			if (dirty & /*value*/ 1) {
    				input.checked = /*value*/ ctx[0];
    			}
    		},
    		i: noop,
    		o: noop,
    		d(detaching) {
    			if (detaching) detach(label);
    			mounted = false;
    			run_all(dispose);
    		}
    	};
    }

    function instance$4($$self, $$props, $$invalidate) {
    	let { value } = $$props;

    	function change_handler(event) {
    		bubble.call(this, $$self, event);
    	}

    	function input_change_handler() {
    		value = this.checked;
    		$$invalidate(0, value);
    	}

    	$$self.$$set = $$props => {
    		if ('value' in $$props) $$invalidate(0, value = $$props.value);
    	};

    	return [value, change_handler, input_change_handler];
    }

    class Slider extends SvelteComponent {
    	constructor(options) {
    		super();
    		init(this, options, instance$4, create_fragment$4, safe_not_equal, { value: 0 });
    	}
    }

    /* ../../frontend/src/lib/Error.svelte generated by Svelte v3.49.0 */

    function create_if_block$3(ctx) {
    	let span;
    	let t;
    	let span_levels = [/*$$restProps*/ ctx[1]];
    	let span_data = {};

    	for (let i = 0; i < span_levels.length; i += 1) {
    		span_data = assign(span_data, span_levels[i]);
    	}

    	return {
    		c() {
    			span = element("span");
    			t = text(/*message*/ ctx[0]);
    			set_attributes(span, span_data);
    			toggle_class(span, "svelte-x8wkw1", true);
    		},
    		m(target, anchor) {
    			insert(target, span, anchor);
    			append(span, t);
    		},
    		p(ctx, dirty) {
    			if (dirty & /*message*/ 1) set_data(t, /*message*/ ctx[0]);
    			set_attributes(span, span_data = get_spread_update(span_levels, [dirty & /*$$restProps*/ 2 && /*$$restProps*/ ctx[1]]));
    			toggle_class(span, "svelte-x8wkw1", true);
    		},
    		d(detaching) {
    			if (detaching) detach(span);
    		}
    	};
    }

    function create_fragment$3(ctx) {
    	let if_block_anchor;
    	let if_block = /*message*/ ctx[0] && create_if_block$3(ctx);

    	return {
    		c() {
    			if (if_block) if_block.c();
    			if_block_anchor = empty();
    		},
    		m(target, anchor) {
    			if (if_block) if_block.m(target, anchor);
    			insert(target, if_block_anchor, anchor);
    		},
    		p(ctx, [dirty]) {
    			if (/*message*/ ctx[0]) {
    				if (if_block) {
    					if_block.p(ctx, dirty);
    				} else {
    					if_block = create_if_block$3(ctx);
    					if_block.c();
    					if_block.m(if_block_anchor.parentNode, if_block_anchor);
    				}
    			} else if (if_block) {
    				if_block.d(1);
    				if_block = null;
    			}
    		},
    		i: noop,
    		o: noop,
    		d(detaching) {
    			if (if_block) if_block.d(detaching);
    			if (detaching) detach(if_block_anchor);
    		}
    	};
    }

    function instance$3($$self, $$props, $$invalidate) {
    	const omit_props_names = ["message"];
    	let $$restProps = compute_rest_props($$props, omit_props_names);
    	let { message } = $$props;

    	$$self.$$set = $$new_props => {
    		$$props = assign(assign({}, $$props), exclude_internal_props($$new_props));
    		$$invalidate(1, $$restProps = compute_rest_props($$props, omit_props_names));
    		if ('message' in $$new_props) $$invalidate(0, message = $$new_props.message);
    	};

    	return [message, $$restProps];
    }

    class Error$1 extends SvelteComponent {
    	constructor(options) {
    		super();
    		init(this, options, instance$3, create_fragment$3, safe_not_equal, { message: 0 });
    	}
    }

    /* ../../frontend/src/lib/Input.svelte generated by Svelte v3.49.0 */

    function create_if_block$2(ctx) {
    	let div;
    	let t;

    	return {
    		c() {
    			div = element("div");
    			t = text(/*suffix*/ ctx[2]);
    			attr(div, "class", "suffix svelte-vvde4q");
    		},
    		m(target, anchor) {
    			insert(target, div, anchor);
    			append(div, t);
    		},
    		p(ctx, dirty) {
    			if (dirty & /*suffix*/ 4) set_data(t, /*suffix*/ ctx[2]);
    		},
    		d(detaching) {
    			if (detaching) detach(div);
    		}
    	};
    }

    function create_fragment$2(ctx) {
    	let div1;
    	let div0;
    	let input;
    	let t0;
    	let t1;
    	let error_1;
    	let updating_message;
    	let current;
    	let mounted;
    	let dispose;
    	let input_levels = [{ value: /*value*/ ctx[0] }, /*$$restProps*/ ctx[5]];
    	let input_data = {};

    	for (let i = 0; i < input_levels.length; i += 1) {
    		input_data = assign(input_data, input_levels[i]);
    	}

    	let if_block = /*suffix*/ ctx[2] && create_if_block$2(ctx);

    	function error_1_message_binding(value) {
    		/*error_1_message_binding*/ ctx[7](value);
    	}

    	let error_1_props = { class: "error" };

    	if (/*error*/ ctx[1] !== void 0) {
    		error_1_props.message = /*error*/ ctx[1];
    	}

    	error_1 = new Error$1({ props: error_1_props });
    	binding_callbacks.push(() => bind(error_1, 'message', error_1_message_binding));

    	return {
    		c() {
    			div1 = element("div");
    			div0 = element("div");
    			input = element("input");
    			t0 = space();
    			if (if_block) if_block.c();
    			t1 = space();
    			create_component(error_1.$$.fragment);
    			set_attributes(input, input_data);
    			toggle_class(input, "error", /*error*/ ctx[1] !== null);
    			toggle_class(input, "logo", /*logo*/ ctx[3] !== null);
    			set_style(input, "background-image", /*logo*/ ctx[3], false);
    			toggle_class(input, "svelte-vvde4q", true);
    			attr(div0, "class", "wrapper svelte-vvde4q");
    			attr(div1, "class", "root svelte-vvde4q");
    		},
    		m(target, anchor) {
    			insert(target, div1, anchor);
    			append(div1, div0);
    			append(div0, input);
    			input.value = input_data.value;
    			if (input.autofocus) input.focus();
    			append(div0, t0);
    			if (if_block) if_block.m(div0, null);
    			append(div1, t1);
    			mount_component(error_1, div1, null);
    			current = true;

    			if (!mounted) {
    				dispose = [
    					listen(input, "input", /*handleInput*/ ctx[4]),
    					listen(input, "change", /*change_handler*/ ctx[6])
    				];

    				mounted = true;
    			}
    		},
    		p(ctx, [dirty]) {
    			set_attributes(input, input_data = get_spread_update(input_levels, [
    				(!current || dirty & /*value*/ 1 && input.value !== /*value*/ ctx[0]) && { value: /*value*/ ctx[0] },
    				dirty & /*$$restProps*/ 32 && /*$$restProps*/ ctx[5]
    			]));

    			if ('value' in input_data) {
    				input.value = input_data.value;
    			}

    			toggle_class(input, "error", /*error*/ ctx[1] !== null);
    			toggle_class(input, "logo", /*logo*/ ctx[3] !== null);
    			set_style(input, "background-image", /*logo*/ ctx[3], false);
    			toggle_class(input, "svelte-vvde4q", true);

    			if (/*suffix*/ ctx[2]) {
    				if (if_block) {
    					if_block.p(ctx, dirty);
    				} else {
    					if_block = create_if_block$2(ctx);
    					if_block.c();
    					if_block.m(div0, null);
    				}
    			} else if (if_block) {
    				if_block.d(1);
    				if_block = null;
    			}

    			const error_1_changes = {};

    			if (!updating_message && dirty & /*error*/ 2) {
    				updating_message = true;
    				error_1_changes.message = /*error*/ ctx[1];
    				add_flush_callback(() => updating_message = false);
    			}

    			error_1.$set(error_1_changes);
    		},
    		i(local) {
    			if (current) return;
    			transition_in(error_1.$$.fragment, local);
    			current = true;
    		},
    		o(local) {
    			transition_out(error_1.$$.fragment, local);
    			current = false;
    		},
    		d(detaching) {
    			if (detaching) detach(div1);
    			if (if_block) if_block.d();
    			destroy_component(error_1);
    			mounted = false;
    			run_all(dispose);
    		}
    	};
    }

    function instance$2($$self, $$props, $$invalidate) {
    	const omit_props_names = ["value","error","suffix","logo"];
    	let $$restProps = compute_rest_props($$props, omit_props_names);
    	let { value = "" } = $$props;
    	let { error = null } = $$props;
    	let { suffix = null } = $$props;
    	let { logo = null } = $$props;

    	function handleInput(e) {
    		$$invalidate(0, value = e.target.value);
    	}

    	function change_handler(event) {
    		bubble.call(this, $$self, event);
    	}

    	function error_1_message_binding(value) {
    		error = value;
    		$$invalidate(1, error);
    	}

    	$$self.$$set = $$new_props => {
    		$$props = assign(assign({}, $$props), exclude_internal_props($$new_props));
    		$$invalidate(5, $$restProps = compute_rest_props($$props, omit_props_names));
    		if ('value' in $$new_props) $$invalidate(0, value = $$new_props.value);
    		if ('error' in $$new_props) $$invalidate(1, error = $$new_props.error);
    		if ('suffix' in $$new_props) $$invalidate(2, suffix = $$new_props.suffix);
    		if ('logo' in $$new_props) $$invalidate(3, logo = $$new_props.logo);
    	};

    	return [
    		value,
    		error,
    		suffix,
    		logo,
    		handleInput,
    		$$restProps,
    		change_handler,
    		error_1_message_binding
    	];
    }

    class Input extends SvelteComponent {
    	constructor(options) {
    		super();
    		init(this, options, instance$2, create_fragment$2, safe_not_equal, { value: 0, error: 1, suffix: 2, logo: 3 });
    	}
    }

    /* Option.svelte generated by Svelte v3.49.0 */

    function create_if_block_2(ctx) {
    	let slider;
    	let updating_value;
    	let current;

    	function slider_value_binding(value) {
    		/*slider_value_binding*/ ctx[6](value);
    	}

    	let slider_props = { name: /*option*/ ctx[0].name };

    	if (/*option*/ ctx[0].value !== void 0) {
    		slider_props.value = /*option*/ ctx[0].value;
    	}

    	slider = new Slider({ props: slider_props });
    	binding_callbacks.push(() => bind(slider, 'value', slider_value_binding));
    	slider.$on("change", /*change_handler_2*/ ctx[7]);

    	return {
    		c() {
    			create_component(slider.$$.fragment);
    		},
    		m(target, anchor) {
    			mount_component(slider, target, anchor);
    			current = true;
    		},
    		p(ctx, dirty) {
    			const slider_changes = {};
    			if (dirty & /*option*/ 1) slider_changes.name = /*option*/ ctx[0].name;

    			if (!updating_value && dirty & /*option*/ 1) {
    				updating_value = true;
    				slider_changes.value = /*option*/ ctx[0].value;
    				add_flush_callback(() => updating_value = false);
    			}

    			slider.$set(slider_changes);
    		},
    		i(local) {
    			if (current) return;
    			transition_in(slider.$$.fragment, local);
    			current = true;
    		},
    		o(local) {
    			transition_out(slider.$$.fragment, local);
    			current = false;
    		},
    		d(detaching) {
    			destroy_component(slider, detaching);
    		}
    	};
    }

    // (20:37) 
    function create_if_block_1$1(ctx) {
    	let input;
    	let updating_value;
    	let current;

    	function input_value_binding(value) {
    		/*input_value_binding*/ ctx[4](value);
    	}

    	let input_props = {
    		type: "number",
    		suffix: /*option*/ ctx[0].suffix
    	};

    	if (/*option*/ ctx[0].value !== void 0) {
    		input_props.value = /*option*/ ctx[0].value;
    	}

    	input = new Input({ props: input_props });
    	binding_callbacks.push(() => bind(input, 'value', input_value_binding));
    	input.$on("change", /*change_handler_1*/ ctx[5]);

    	return {
    		c() {
    			create_component(input.$$.fragment);
    		},
    		m(target, anchor) {
    			mount_component(input, target, anchor);
    			current = true;
    		},
    		p(ctx, dirty) {
    			const input_changes = {};
    			if (dirty & /*option*/ 1) input_changes.suffix = /*option*/ ctx[0].suffix;

    			if (!updating_value && dirty & /*option*/ 1) {
    				updating_value = true;
    				input_changes.value = /*option*/ ctx[0].value;
    				add_flush_callback(() => updating_value = false);
    			}

    			input.$set(input_changes);
    		},
    		i(local) {
    			if (current) return;
    			transition_in(input.$$.fragment, local);
    			current = true;
    		},
    		o(local) {
    			transition_out(input.$$.fragment, local);
    			current = false;
    		},
    		d(detaching) {
    			destroy_component(input, detaching);
    		}
    	};
    }

    // (18:2) {#if option.type === 'text'}
    function create_if_block$1(ctx) {
    	let input;
    	let input_name_value;
    	let mounted;
    	let dispose;

    	return {
    		c() {
    			input = element("input");
    			attr(input, "type", "text");
    			attr(input, "name", input_name_value = /*option*/ ctx[0].name);
    			attr(input, "class", "svelte-skg0la");
    		},
    		m(target, anchor) {
    			insert(target, input, anchor);
    			set_input_value(input, /*option*/ ctx[0].value);

    			if (!mounted) {
    				dispose = [
    					listen(input, "input", /*input_input_handler*/ ctx[3]),
    					listen(input, "change", /*change_handler*/ ctx[2])
    				];

    				mounted = true;
    			}
    		},
    		p(ctx, dirty) {
    			if (dirty & /*option*/ 1 && input_name_value !== (input_name_value = /*option*/ ctx[0].name)) {
    				attr(input, "name", input_name_value);
    			}

    			if (dirty & /*option*/ 1 && input.value !== /*option*/ ctx[0].value) {
    				set_input_value(input, /*option*/ ctx[0].value);
    			}
    		},
    		i: noop,
    		o: noop,
    		d(detaching) {
    			if (detaching) detach(input);
    			mounted = false;
    			run_all(dispose);
    		}
    	};
    }

    function create_fragment$1(ctx) {
    	let div;
    	let label;
    	let span0;
    	let t0_value = /*option*/ ctx[0].description + "";
    	let t0;
    	let span1;
    	let label_for_value;
    	let t2;
    	let current_block_type_index;
    	let if_block;
    	let current;
    	let mounted;
    	let dispose;
    	const if_block_creators = [create_if_block$1, create_if_block_1$1, create_if_block_2];
    	const if_blocks = [];

    	function select_block_type(ctx, dirty) {
    		if (/*option*/ ctx[0].type === 'text') return 0;
    		if (/*option*/ ctx[0].type === 'number') return 1;
    		if (/*option*/ ctx[0].type === 'checkbox') return 2;
    		return -1;
    	}

    	if (~(current_block_type_index = select_block_type(ctx))) {
    		if_block = if_blocks[current_block_type_index] = if_block_creators[current_block_type_index](ctx);
    	}

    	return {
    		c() {
    			div = element("div");
    			label = element("label");
    			span0 = element("span");
    			t0 = text(t0_value);
    			span1 = element("span");
    			span1.textContent = "⟲";
    			t2 = space();
    			if (if_block) if_block.c();
    			attr(span1, "class", "reset svelte-skg0la");
    			attr(span1, "title", "Reset to default");
    			attr(label, "for", label_for_value = /*option*/ ctx[0].name);
    			attr(label, "class", "svelte-skg0la");
    			attr(div, "class", "svelte-skg0la");
    		},
    		m(target, anchor) {
    			insert(target, div, anchor);
    			append(div, label);
    			append(label, span0);
    			append(span0, t0);
    			append(label, span1);
    			append(div, t2);

    			if (~current_block_type_index) {
    				if_blocks[current_block_type_index].m(div, null);
    			}

    			current = true;

    			if (!mounted) {
    				dispose = listen(span1, "click", /*reset*/ ctx[1]);
    				mounted = true;
    			}
    		},
    		p(ctx, [dirty]) {
    			if ((!current || dirty & /*option*/ 1) && t0_value !== (t0_value = /*option*/ ctx[0].description + "")) set_data(t0, t0_value);

    			if (!current || dirty & /*option*/ 1 && label_for_value !== (label_for_value = /*option*/ ctx[0].name)) {
    				attr(label, "for", label_for_value);
    			}

    			let previous_block_index = current_block_type_index;
    			current_block_type_index = select_block_type(ctx);

    			if (current_block_type_index === previous_block_index) {
    				if (~current_block_type_index) {
    					if_blocks[current_block_type_index].p(ctx, dirty);
    				}
    			} else {
    				if (if_block) {
    					group_outros();

    					transition_out(if_blocks[previous_block_index], 1, 1, () => {
    						if_blocks[previous_block_index] = null;
    					});

    					check_outros();
    				}

    				if (~current_block_type_index) {
    					if_block = if_blocks[current_block_type_index];

    					if (!if_block) {
    						if_block = if_blocks[current_block_type_index] = if_block_creators[current_block_type_index](ctx);
    						if_block.c();
    					} else {
    						if_block.p(ctx, dirty);
    					}

    					transition_in(if_block, 1);
    					if_block.m(div, null);
    				} else {
    					if_block = null;
    				}
    			}
    		},
    		i(local) {
    			if (current) return;
    			transition_in(if_block);
    			current = true;
    		},
    		o(local) {
    			transition_out(if_block);
    			current = false;
    		},
    		d(detaching) {
    			if (detaching) detach(div);

    			if (~current_block_type_index) {
    				if_blocks[current_block_type_index].d();
    			}

    			mounted = false;
    			dispose();
    		}
    	};
    }

    function instance$1($$self, $$props, $$invalidate) {
    	let { option } = $$props;
    	const dispatch = createEventDispatcher();

    	function reset() {
    		$$invalidate(0, option.value = option.default, option);
    		dispatch('change');
    	}

    	function change_handler(event) {
    		bubble.call(this, $$self, event);
    	}

    	function input_input_handler() {
    		option.value = this.value;
    		$$invalidate(0, option);
    	}

    	function input_value_binding(value) {
    		if ($$self.$$.not_equal(option.value, value)) {
    			option.value = value;
    			$$invalidate(0, option);
    		}
    	}

    	function change_handler_1(event) {
    		bubble.call(this, $$self, event);
    	}

    	function slider_value_binding(value) {
    		if ($$self.$$.not_equal(option.value, value)) {
    			option.value = value;
    			$$invalidate(0, option);
    		}
    	}

    	function change_handler_2(event) {
    		bubble.call(this, $$self, event);
    	}

    	$$self.$$set = $$props => {
    		if ('option' in $$props) $$invalidate(0, option = $$props.option);
    	};

    	return [
    		option,
    		reset,
    		change_handler,
    		input_input_handler,
    		input_value_binding,
    		change_handler_1,
    		slider_value_binding,
    		change_handler_2
    	];
    }

    class Option extends SvelteComponent {
    	constructor(options) {
    		super();
    		init(this, options, instance$1, create_fragment$1, safe_not_equal, { option: 0 });
    	}
    }

    const browser = globalThis.browser || globalThis.chrome;

    async function callBackground(request) {
      console.log("sending to service worker", request);
      return await new Promise((resolve, reject) => {
        browser.runtime.sendMessage(request, response => {
          console.log("response from service worker", response);
          if (response === undefined) {
            reject(browser.runtime.lastError);
          } else if (response.status === "error") {
            // TODO: use something like serialize-error
            reject(new Error(response.error));
          } else {
            resolve(response.response);
          }
        });
      });
    }

    const worker = new Proxy({}, {
      get(obj, prop) {
        return async function () {
          return await callBackground({command: prop, args: Array.from(arguments)});
        };
      }
    });

    async function getCurrentTab() {
      const queryOptions = { active: true, lastFocusedWindow: true };
      // `tab` will either be a `tabs.Tab` instance or `undefined`.
      // NOTE: chrome.tabs.query doesn't work here - it returns undefined
      const [tab] = await browser.tabs.query(queryOptions);
      if (tab === undefined)
        throw new Error("could not find current tab");
      return tab;
    }

    new Proxy({}, {
      get(obj, prop) {
        return async function () {
          const tab = await getCurrentTab();
          const msg = {command: prop, args: Array.from(arguments)};
          console.log("sending to tab", tab, msg);
          return await browser.tabs.sendMessage(tab.id, msg);
        };
      }
    });

    /* Options.svelte generated by Svelte v3.49.0 */

    function get_each_context(ctx, list, i) {
    	const child_ctx = ctx.slice();
    	child_ctx[5] = list[i];
    	child_ctx[6] = list;
    	child_ctx[7] = i;
    	return child_ctx;
    }

    function get_each_context_1(ctx, list, i) {
    	const child_ctx = ctx.slice();
    	child_ctx[5] = list[i];
    	child_ctx[8] = list;
    	child_ctx[9] = i;
    	return child_ctx;
    }

    // (1:0) <script>   import Option from "./Option.svelte";   import {worker}
    function create_catch_block(ctx) {
    	return {
    		c: noop,
    		m: noop,
    		p: noop,
    		i: noop,
    		o: noop,
    		d: noop
    	};
    }

    // (24:22)    <div class=options>     {#each options as option}
    function create_then_block(ctx) {
    	let div0;
    	let t0;
    	let details;
    	let summary;
    	let t2;
    	let div1;
    	let current;
    	let each_value_1 = /*options*/ ctx[0];
    	let each_blocks_1 = [];

    	for (let i = 0; i < each_value_1.length; i += 1) {
    		each_blocks_1[i] = create_each_block_1(get_each_context_1(ctx, each_value_1, i));
    	}

    	const out = i => transition_out(each_blocks_1[i], 1, 1, () => {
    		each_blocks_1[i] = null;
    	});

    	let each_value = /*options*/ ctx[0];
    	let each_blocks = [];

    	for (let i = 0; i < each_value.length; i += 1) {
    		each_blocks[i] = create_each_block(get_each_context(ctx, each_value, i));
    	}

    	const out_1 = i => transition_out(each_blocks[i], 1, 1, () => {
    		each_blocks[i] = null;
    	});

    	return {
    		c() {
    			div0 = element("div");

    			for (let i = 0; i < each_blocks_1.length; i += 1) {
    				each_blocks_1[i].c();
    			}

    			t0 = space();
    			details = element("details");
    			summary = element("summary");
    			summary.textContent = "Developer options";
    			t2 = space();
    			div1 = element("div");

    			for (let i = 0; i < each_blocks.length; i += 1) {
    				each_blocks[i].c();
    			}

    			attr(div0, "class", "options svelte-chtpbg");
    			attr(div1, "class", "options svelte-chtpbg");
    		},
    		m(target, anchor) {
    			insert(target, div0, anchor);

    			for (let i = 0; i < each_blocks_1.length; i += 1) {
    				each_blocks_1[i].m(div0, null);
    			}

    			insert(target, t0, anchor);
    			insert(target, details, anchor);
    			append(details, summary);
    			append(details, t2);
    			append(details, div1);

    			for (let i = 0; i < each_blocks.length; i += 1) {
    				each_blocks[i].m(div1, null);
    			}

    			current = true;
    		},
    		p(ctx, dirty) {
    			if (dirty & /*options, save*/ 3) {
    				each_value_1 = /*options*/ ctx[0];
    				let i;

    				for (i = 0; i < each_value_1.length; i += 1) {
    					const child_ctx = get_each_context_1(ctx, each_value_1, i);

    					if (each_blocks_1[i]) {
    						each_blocks_1[i].p(child_ctx, dirty);
    						transition_in(each_blocks_1[i], 1);
    					} else {
    						each_blocks_1[i] = create_each_block_1(child_ctx);
    						each_blocks_1[i].c();
    						transition_in(each_blocks_1[i], 1);
    						each_blocks_1[i].m(div0, null);
    					}
    				}

    				group_outros();

    				for (i = each_value_1.length; i < each_blocks_1.length; i += 1) {
    					out(i);
    				}

    				check_outros();
    			}

    			if (dirty & /*options, save*/ 3) {
    				each_value = /*options*/ ctx[0];
    				let i;

    				for (i = 0; i < each_value.length; i += 1) {
    					const child_ctx = get_each_context(ctx, each_value, i);

    					if (each_blocks[i]) {
    						each_blocks[i].p(child_ctx, dirty);
    						transition_in(each_blocks[i], 1);
    					} else {
    						each_blocks[i] = create_each_block(child_ctx);
    						each_blocks[i].c();
    						transition_in(each_blocks[i], 1);
    						each_blocks[i].m(div1, null);
    					}
    				}

    				group_outros();

    				for (i = each_value.length; i < each_blocks.length; i += 1) {
    					out_1(i);
    				}

    				check_outros();
    			}
    		},
    		i(local) {
    			if (current) return;

    			for (let i = 0; i < each_value_1.length; i += 1) {
    				transition_in(each_blocks_1[i]);
    			}

    			for (let i = 0; i < each_value.length; i += 1) {
    				transition_in(each_blocks[i]);
    			}

    			current = true;
    		},
    		o(local) {
    			each_blocks_1 = each_blocks_1.filter(Boolean);

    			for (let i = 0; i < each_blocks_1.length; i += 1) {
    				transition_out(each_blocks_1[i]);
    			}

    			each_blocks = each_blocks.filter(Boolean);

    			for (let i = 0; i < each_blocks.length; i += 1) {
    				transition_out(each_blocks[i]);
    			}

    			current = false;
    		},
    		d(detaching) {
    			if (detaching) detach(div0);
    			destroy_each(each_blocks_1, detaching);
    			if (detaching) detach(t0);
    			if (detaching) detach(details);
    			destroy_each(each_blocks, detaching);
    		}
    	};
    }

    // (27:6) {#if !option.dev}
    function create_if_block_1(ctx) {
    	let option;
    	let updating_option;
    	let current;

    	function option_option_binding(value) {
    		/*option_option_binding*/ ctx[3](value, /*option*/ ctx[5], /*each_value_1*/ ctx[8], /*option_index_1*/ ctx[9]);
    	}

    	let option_props = {};

    	if (/*option*/ ctx[5] !== void 0) {
    		option_props.option = /*option*/ ctx[5];
    	}

    	option = new Option({ props: option_props });
    	binding_callbacks.push(() => bind(option, 'option', option_option_binding));
    	option.$on("change", /*save*/ ctx[1]);

    	return {
    		c() {
    			create_component(option.$$.fragment);
    		},
    		m(target, anchor) {
    			mount_component(option, target, anchor);
    			current = true;
    		},
    		p(new_ctx, dirty) {
    			ctx = new_ctx;
    			const option_changes = {};

    			if (!updating_option && dirty & /*options*/ 1) {
    				updating_option = true;
    				option_changes.option = /*option*/ ctx[5];
    				add_flush_callback(() => updating_option = false);
    			}

    			option.$set(option_changes);
    		},
    		i(local) {
    			if (current) return;
    			transition_in(option.$$.fragment, local);
    			current = true;
    		},
    		o(local) {
    			transition_out(option.$$.fragment, local);
    			current = false;
    		},
    		d(detaching) {
    			destroy_component(option, detaching);
    		}
    	};
    }

    // (26:4) {#each options as option}
    function create_each_block_1(ctx) {
    	let if_block_anchor;
    	let current;
    	let if_block = !/*option*/ ctx[5].dev && create_if_block_1(ctx);

    	return {
    		c() {
    			if (if_block) if_block.c();
    			if_block_anchor = empty();
    		},
    		m(target, anchor) {
    			if (if_block) if_block.m(target, anchor);
    			insert(target, if_block_anchor, anchor);
    			current = true;
    		},
    		p(ctx, dirty) {
    			if (!/*option*/ ctx[5].dev) {
    				if (if_block) {
    					if_block.p(ctx, dirty);

    					if (dirty & /*options*/ 1) {
    						transition_in(if_block, 1);
    					}
    				} else {
    					if_block = create_if_block_1(ctx);
    					if_block.c();
    					transition_in(if_block, 1);
    					if_block.m(if_block_anchor.parentNode, if_block_anchor);
    				}
    			} else if (if_block) {
    				group_outros();

    				transition_out(if_block, 1, 1, () => {
    					if_block = null;
    				});

    				check_outros();
    			}
    		},
    		i(local) {
    			if (current) return;
    			transition_in(if_block);
    			current = true;
    		},
    		o(local) {
    			transition_out(if_block);
    			current = false;
    		},
    		d(detaching) {
    			if (if_block) if_block.d(detaching);
    			if (detaching) detach(if_block_anchor);
    		}
    	};
    }

    // (36:8) {#if option.dev}
    function create_if_block(ctx) {
    	let option;
    	let updating_option;
    	let current;

    	function option_option_binding_1(value) {
    		/*option_option_binding_1*/ ctx[4](value, /*option*/ ctx[5], /*each_value*/ ctx[6], /*option_index*/ ctx[7]);
    	}

    	let option_props = {};

    	if (/*option*/ ctx[5] !== void 0) {
    		option_props.option = /*option*/ ctx[5];
    	}

    	option = new Option({ props: option_props });
    	binding_callbacks.push(() => bind(option, 'option', option_option_binding_1));
    	option.$on("change", /*save*/ ctx[1]);

    	return {
    		c() {
    			create_component(option.$$.fragment);
    		},
    		m(target, anchor) {
    			mount_component(option, target, anchor);
    			current = true;
    		},
    		p(new_ctx, dirty) {
    			ctx = new_ctx;
    			const option_changes = {};

    			if (!updating_option && dirty & /*options*/ 1) {
    				updating_option = true;
    				option_changes.option = /*option*/ ctx[5];
    				add_flush_callback(() => updating_option = false);
    			}

    			option.$set(option_changes);
    		},
    		i(local) {
    			if (current) return;
    			transition_in(option.$$.fragment, local);
    			current = true;
    		},
    		o(local) {
    			transition_out(option.$$.fragment, local);
    			current = false;
    		},
    		d(detaching) {
    			destroy_component(option, detaching);
    		}
    	};
    }

    // (35:6) {#each options as option}
    function create_each_block(ctx) {
    	let if_block_anchor;
    	let current;
    	let if_block = /*option*/ ctx[5].dev && create_if_block(ctx);

    	return {
    		c() {
    			if (if_block) if_block.c();
    			if_block_anchor = empty();
    		},
    		m(target, anchor) {
    			if (if_block) if_block.m(target, anchor);
    			insert(target, if_block_anchor, anchor);
    			current = true;
    		},
    		p(ctx, dirty) {
    			if (/*option*/ ctx[5].dev) {
    				if (if_block) {
    					if_block.p(ctx, dirty);

    					if (dirty & /*options*/ 1) {
    						transition_in(if_block, 1);
    					}
    				} else {
    					if_block = create_if_block(ctx);
    					if_block.c();
    					transition_in(if_block, 1);
    					if_block.m(if_block_anchor.parentNode, if_block_anchor);
    				}
    			} else if (if_block) {
    				group_outros();

    				transition_out(if_block, 1, 1, () => {
    					if_block = null;
    				});

    				check_outros();
    			}
    		},
    		i(local) {
    			if (current) return;
    			transition_in(if_block);
    			current = true;
    		},
    		o(local) {
    			transition_out(if_block);
    			current = false;
    		},
    		d(detaching) {
    			if (if_block) if_block.d(detaching);
    			if (detaching) detach(if_block_anchor);
    		}
    	};
    }

    // (1:0) <script>   import Option from "./Option.svelte";   import {worker}
    function create_pending_block(ctx) {
    	return {
    		c: noop,
    		m: noop,
    		p: noop,
    		i: noop,
    		o: noop,
    		d: noop
    	};
    }

    function create_fragment(ctx) {
    	let main;
    	let h1;
    	let t1;
    	let current;

    	let info = {
    		ctx,
    		current: null,
    		token: null,
    		hasCatch: false,
    		pending: create_pending_block,
    		then: create_then_block,
    		catch: create_catch_block,
    		blocks: [,,,]
    	};

    	handle_promise(/*load*/ ctx[2](), info);

    	return {
    		c() {
    			main = element("main");
    			h1 = element("h1");
    			h1.textContent = "Settings";
    			t1 = space();
    			info.block.c();
    			attr(h1, "class", "svelte-chtpbg");
    			attr(main, "class", "svelte-chtpbg");
    		},
    		m(target, anchor) {
    			insert(target, main, anchor);
    			append(main, h1);
    			append(main, t1);
    			info.block.m(main, info.anchor = null);
    			info.mount = () => main;
    			info.anchor = null;
    			current = true;
    		},
    		p(new_ctx, [dirty]) {
    			ctx = new_ctx;
    			update_await_block_branch(info, ctx, dirty);
    		},
    		i(local) {
    			if (current) return;
    			transition_in(info.block);
    			current = true;
    		},
    		o(local) {
    			for (let i = 0; i < 3; i += 1) {
    				const block = info.blocks[i];
    				transition_out(block);
    			}

    			current = false;
    		},
    		d(detaching) {
    			if (detaching) detach(main);
    			info.block.d();
    			info.token = null;
    			info = null;
    		}
    	};
    }

    function instance($$self, $$props, $$invalidate) {
    	let options = [];

    	async function save() {
    		let values = {};

    		for (const option of options) {
    			values[option.name] = option.value;
    		}

    		await worker.saveOptions(values);
    	}

    	async function load() {
    		console.log("loading");
    		$$invalidate(0, options = await worker.loadOptions());
    		console.log("options", options);
    	}

    	function option_option_binding(value, option, each_value_1, option_index_1) {
    		each_value_1[option_index_1] = value;
    		$$invalidate(0, options);
    	}

    	function option_option_binding_1(value, option, each_value, option_index) {
    		each_value[option_index] = value;
    		$$invalidate(0, options);
    	}

    	return [options, save, load, option_option_binding, option_option_binding_1];
    }

    class Options extends SvelteComponent {
    	constructor(options) {
    		super();
    		init(this, options, instance, create_fragment, safe_not_equal, {});
    	}
    }

    const app = new Options({ target: document.body });

    return app;

})();
//# sourceMappingURL=options.js.map
