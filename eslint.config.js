import tsParser from '@typescript-eslint/parser'

/** @type {import('eslint').Linter.Config[]} */
export default [
  // All TypeScript files: set the parser
  {
    files: ['**/*.ts'],
    languageOptions: {
      parser: tsParser,
    },
  },
  // packages/** — the core rule: no obsidian imports ever
  {
    files: ['100-Source/packages/**/*.ts'],
    rules: {
      'no-restricted-imports': [
        'error',
        {
          paths: ['obsidian'],
          patterns: ['@codemirror/*', '@lezer/*'],
        },
      ],
    },
  },
]
