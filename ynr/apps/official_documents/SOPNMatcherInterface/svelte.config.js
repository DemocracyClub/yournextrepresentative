import { vitePreprocess } from '@sveltejs/vite-plugin-svelte';


export default {
  pages: {
    index: {
    preprocess: vitePreprocess(),
      entry: 'src/main.js',
      template: 'index.html',
      filename: 'index.html',
      title: 'Index Page',
    },
  },
  filenameHashing: false

};
