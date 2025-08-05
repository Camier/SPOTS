import js from '@eslint/js';

export default [
  js.configs.recommended,
  {
    files: ['src/frontend/js/**/*.js'],
    rules: {
      'no-unused-vars': 'warn',
      'no-console': 'off',
      'no-undef': 'off', // Browser globals
    },
    languageOptions: {
      ecmaVersion: 2022,
      sourceType: 'module',
      globals: {
        window: 'readonly',
        document: 'readonly',
        console: 'readonly',
        L: 'readonly', // Leaflet global
        navigator: 'readonly',
        localStorage: 'readonly',
        sessionStorage: 'readonly',
        fetch: 'readonly',
        URL: 'readonly',
        URLSearchParams: 'readonly',
        FormData: 'readonly',
        Image: 'readonly',
        Worker: 'readonly',
        ServiceWorker: 'readonly',
        caches: 'readonly',
        importScripts: 'readonly',
        self: 'readonly',
      }
    }
  }
];