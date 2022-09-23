import svelte from "rollup-plugin-svelte";
import commonjs from "@rollup/plugin-commonjs";
import resolve from "@rollup/plugin-node-resolve";
import alias from '@rollup/plugin-alias';
import html from '@web/rollup-plugin-html';
import css from "rollup-plugin-css-only";
import copy from 'rollup-plugin-copy';
import path from "path";

const dev = process.env.ROLLUP_WATCH;

function serve() {
  let server;

  function toExit() {
    if (server) server.kill(0);
  }

  return {
    writeBundle() {
      if (server) return;
      server = require("child_process").spawn(
        "npm",
        ["run", "start", "--", "--dev"],
        {
          stdio: ["ignore", "inherit", "inherit"],
          shell: true,
        }
      );

      process.on("SIGTERM", toExit);
      process.on("exit", toExit);
    },
  };
}

function makeOutput(browser) {
  return {
    sourcemap: true,
    format: "iife",
    name: "app",
    dir: `../${browser}/dist`,
  }
}

function makeConfig(name) {
  return {
    input: `${name}.js`,
    output: [
      makeOutput('chrome'),
      makeOutput('firefox'),
    ],
    plugins: [
      svelte({
        compilerOptions: {
          dev: dev,
        },
      }),
      // we'll extract any component CSS out into
      // a separate file - better for performance
      css({ output: `${name}.css` }),

      // If you have external dependencies installed from
      // npm, you'll most likely need these plugins. In
      // some cases you'll need additional configuration -
      // consult the documentation for details:
      // https://github.com/rollup/plugins/tree/master/packages/commonjs
      resolve({
        browser: true,
        dedupe: ["svelte"],
      }),
      commonjs(),
      alias({
        entries: {
          '$lib': path.resolve(__dirname, '../../frontend/src/lib'),
        },
      }),
      copy({
        targets: [
          { src: `${name}.html`, dest: ["../chrome/dist", "../firefox/dist"] },
        ],
      }),
    ],
    watch: {
      clearScreen: false,
    },
  }
}

function makeHtmlConfig() {
  return {
    input: 'popup.html',
    output: { dir: '../chrome/dist' },
    plugins: [
      svelte(),
      css({ output: `popup.css` }),
      resolve({
        browser: true,
        dedupe: ["svelte"],
      }),
      commonjs(),
      alias({
        entries: {
          '$lib': path.resolve(__dirname, '../../frontend/src/lib'),
        },
      }),
      html(),
    ],
  }
}

function staticFile(filename) {
  return {
    src: `static/${filename}`,
    dest: ["../chrome/dist/static", "../firefox/dist/static"],
  }
}

function manifestFile(src, dest, transform) {
  return {
    src: src,
    dest: path.dirname(dest),
    rename: "manifest.json",
    transform: (contents, filename) => JSON.stringify(transform(JSON.parse(contents))),
  }
}

function patchChromeManifest(json) {
  json.host_permissions = [...json.host_permissions, 'http://localhost/*'];
  return json;
}

function patchFirefoxManifest(json) {
  json.permissions = [...json.permissions, 'http://localhost/*'];
  return json;
}


export default [
  makeConfig('options'),
  makeConfig('popup'),
  makeConfig('window'),
  makeConfig('background'),
  makeConfig('contentscript'),
  makeConfig('pagescript'),
  {
    input: "./empty.js",
    output: [
      makeOutput('chrome'),
      makeOutput('firefox'),
    ],
    plugins: [
      resolve({
        browser: true,
      }),
      copy({
        targets: [
          staticFile("D.svg"),
          staticFile("Inter.var.woff2"),
          staticFile("global.css"),
          staticFile("inter.css"),
          staticFile("D-*.png"),
          manifestFile("manifest-firefox.json", "../firefox/dist/manifest.json", patchFirefoxManifest),
          manifestFile("manifest-chrome.json", "../chrome/dist/manifest.json", patchChromeManifest),
        ],
        verbose: true,
      }),
    ],
  },
];
