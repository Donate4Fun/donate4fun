import svelte from "rollup-plugin-svelte";
import commonjs from "@rollup/plugin-commonjs";
import resolve from "@rollup/plugin-node-resolve";
import alias from '@rollup/plugin-alias';
import replace from "@rollup/plugin-replace";
import copy from '@guanghechen/rollup-plugin-copy';
import styles from "rollup-plugin-styles";
import path from "path";
import fs from "fs";

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

function makeOutput(browser, options) {
  return {
    sourcemap: dev,
    format: "iife",
    name: "app",
    dir: path.join('..', browser, options?.dir || '.'),
    assetFileNames: "[name][extname]",
    footer: options?.footer,
  }
}

function makeConfig(name, options) {
  return {
    input: `${name}.js`,
    output: [
      makeOutput('chrome', options),
      makeOutput('firefox', options),
    ],
    plugins: [
      svelte({
        compilerOptions: {
          dev: dev,
        },
      }),
      // we'll extract any component CSS out into
      // a separate file - better for performance
      //css({ output: `${name}.css` }),
      styles({mode: ["extract", `${name}.css`]}),

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
      replace({
        "process.env.NODE_ENV": JSON.stringify(process.env.NODE_ENV),
        "import.meta.env.DEV": dev,
        preventAssignment: false,
      }),
      copy({
        targets: [
          { src: `${name}.html`, dest: ["../chrome", "../firefox"] },
        ],
      }),
    ],
    watch: {
      clearScreen: false,
    },
  }
}

function staticFile(filename) {
  return {
    src: `static/${filename}`,
    dest: ["../chrome/static", "../firefox/static"],
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

function getVersion() {
  return JSON.parse(fs.readFileSync("package.json")).version;
}

function patchChromeManifest(json) {
  if (dev) {
    json.host_permissions = [...json.host_permissions, '*://localhost/'];
    json.web_accessible_resources[1].matches = [...json.web_accessible_resources[1].matches, 'http://localhost:3000/*'];
    json.content_scripts[1].matches = [...json.content_scripts[1].matches, 'http://localhost:3000/*'];
  }
  json.version = getVersion();
  return json;
}

function patchFirefoxManifest(json) {
  if (dev) {
    // Use *:// instead of http:// because firefox does not allow to get secure cookies for http://localhost
    json.permissions = [...json.permissions, '*://localhost/*'];
    json.content_scripts[1].matches = [...json.content_scripts[1].matches, 'http://localhost/*'];
  }
  json.version = getVersion();
  return json;
}

export default [
  makeConfig('options'),
  makeConfig('popup'),
  makeConfig('window'),
  makeConfig('background'),
  makeConfig('contentscript', {footer: "app;"}), // we need to return pormise from contentscript.js to wait in scripting.executeScript
  makeConfig('contentscripts/donate4.fun', {dir: 'contentscripts'}),
  makeConfig('webln'),
  makeConfig('globalobj'),
  {
    input: "./empty.js",
    treeshake: false,
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
          staticFile("defaults.css"),
          staticFile("D-*.png"),
          staticFile("lottie-arrow.json"),
          staticFile("youtube.svg"),
          staticFile("checkbox.svg"),
          { src: "background.html", dest: "../firefox" },
          manifestFile("manifest-firefox.json", "../firefox/manifest.json", patchFirefoxManifest),
          manifestFile("manifest-chrome.json", "../chrome/manifest.json", patchChromeManifest),
        ],
        verbose: true,
      }),
    ],
  },
];
