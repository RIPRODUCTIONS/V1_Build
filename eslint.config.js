// eslint.config.js
// Flat-config ESLint 9+
// Scoped to source-only to avoid linting build artifacts
import tseslint from '@typescript-eslint/eslint-plugin';
import tsparser from '@typescript-eslint/parser';
import prettier from 'eslint-config-prettier';
import react from 'eslint-plugin-react';
import reactHooks from 'eslint-plugin-react-hooks';
import unusedImports from 'eslint-plugin-unused-imports';
import importPlugin from 'eslint-plugin-import';
import simpleImportSort from 'eslint-plugin-simple-import-sort';
import globals from 'globals';

export default [
  // Restrict linting to app source only and ignore vendor/build blobs
  {
    files: ['apps/**/src/**/*.{ts,tsx,js,jsx}'],
    ignores: [
      '**/node_modules/**',
      '**/.next/**',
      '**/dist/**',
      '**/build/**',
      '**/coverage/**',
      '**/out/**',
      '**/public/**',
      '**/*min*.js',
      '**/*vendor*.js',
      '**/*bundle*.js',
      '**/*.map',
    ],
    languageOptions: {
      ecmaVersion: 'latest',
      sourceType: 'module',
      globals: {
        ...globals.browser,
        ...globals.node,
      },
    },
  },

  // TypeScript + React rules scoped to web app source and tests
  {
    files: ['apps/web/src/**/*.{ts,tsx}', 'apps/web/tests/**/*.{ts,tsx}'],
    ignores: ['**/*.d.ts'],
    languageOptions: {
      parser: tsparser,
      parserOptions: {
        // project-less for speed; re-enable when needed
        ecmaFeatures: { jsx: true },
        sourceType: 'module',
        tsconfigRootDir: import.meta.dirname,
      },
      globals: { React: 'writable' },
    },
    plugins: {
      '@typescript-eslint': tseslint,
      react,
      'react-hooks': reactHooks,
      'unused-imports': unusedImports,
      import: importPlugin,
      'simple-import-sort': simpleImportSort,
    },
    rules: {
      // Leverage TS for undefineds; avoids false positives on DOM/Node types
      'no-undef': 'off',

      // Hygiene
      'no-unused-vars': 'off',
      '@typescript-eslint/no-unused-vars': 'off',
      'unused-imports/no-unused-imports': 'error',
      'unused-imports/no-unused-vars': [
        'error',
        { args: 'after-used', argsIgnorePattern: '^_', varsIgnorePattern: '^_' },
      ],

      // Safer TS
      '@typescript-eslint/no-explicit-any': ['error', { ignoreRestArgs: true }],
      '@typescript-eslint/ban-ts-comment': ['warn', { 'ts-ignore': 'allow-with-description' }],

      // React/JSX
      'react/jsx-uses-react': 'off',
      'react/react-in-jsx-scope': 'off',
      'react-hooks/rules-of-hooks': 'error',
      'react-hooks/exhaustive-deps': 'error',

      // Import hygiene and sorting
      'import/first': 'error',
      'import/newline-after-import': ['error', { count: 1 }],
      'import/no-duplicates': 'error',
      'simple-import-sort/imports': 'error',
      'simple-import-sort/exports': 'error',
    },
    settings: {
      react: { version: 'detect' },
      'import/resolver': {
        typescript: {
          project: './apps/web/tsconfig.json',
        },
      },
    },
  },

  // Keep ESLint from fighting Prettier
  prettier,
];
