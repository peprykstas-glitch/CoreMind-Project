/** @type {import('postcss-load-config').Config} */
const config = {
  plugins: {
    // 👇 БУЛО: tailwindcss: {},
    // 👇 СТАЛО (для нової версії):
    "@tailwindcss/postcss": {}, 
    autoprefixer: {},
  },
};

export default config;