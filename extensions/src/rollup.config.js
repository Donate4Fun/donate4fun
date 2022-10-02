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

function makeOutput(browser, footer) {
  return {
    sourcemap: dev,
    format: "iife",
    name: "app",
    dir: `../${browser}`,
    assetFileNames: "[name][extname]",
    footer: footer,
  }
}

function makeConfig(name, footer) {
  return {
    input: `${name}.js`,
    output: [
      makeOutput('chrome', footer),
      makeOutput('firefox', footer),
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
        preventAssignment: false,
      }),
      copy({
        targets: [
          { src: `${name}.html`, dest: ["../chrome", "../firefox"] },
        ],
      }),
      /*{
        writeBundle(options, bundle){
          if (bundle.fileName === 'contentscript.js")
          for (const [fileName, chunkOrAsset] of Object.entries(bundle)) {
            console.log("writeBundle", fileName, chunkOrAsset);
            //test for file you want to modify
            //const data = fs.readFileSync(fileName, {encoding:'utf8'});
            //data.replace(/^[^\n]*\n/,'');
            //fs.writeFileSync(...)
          }
        },
      },*/
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
  if (dev)
    json.host_permissions = [...json.host_permissions, 'http://localhost/*'];
  json.version = getVersion();
  return json;
}

function patchFirefoxManifest(json) {
  if (dev)
    json.permissions = [...json.permissions, 'http://localhost/*'];
  json.version = getVersion();
  return json;
}


export default [
  makeConfig('options'),
  makeConfig('popup'),
  makeConfig('window'),
  makeConfig('background'),
  makeConfig('contentscript', "app;"), // we need to return pormise from contentscript.js to wait in scripting.executeScript
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
          staticFile("defaults.css"),
          staticFile("D-*.png"),
          staticFile("lottie-arrow.json"),
          staticFile("youtube.svg"),
          { src: "background.html", dest: "../firefox" },
          manifestFile("manifest-firefox.json", "../firefox/manifest.json", patchFirefoxManifest),
          manifestFile("manifest-chrome.json", "../chrome/manifest.json", patchChromeManifest),
        ],
        verbose: true,
      }),
    ],
  },
];
