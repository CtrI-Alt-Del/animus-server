const ALLOWED_TYPES = [
  'build',
  'chore',
  'ci',
  'docs',
  'feat',
  'fix',
  'perf',
  'refactor',
  'revert',
  'style',
  'test',
]

const HEADER_PATTERN =
  /^(build|chore|ci|docs|feat|fix|perf|refactor|revert|style|test)(\([a-z0-9._\/-]+\))?!?: [A-Z][A-Z0-9]+-\d+ .+$/

module.exports = {
  extends: ['@commitlint/config-conventional'],
  plugins: [
    {
      rules: {
        'jira-ticket-required': (parsed) => {
          const header = parsed.header || ''
          const isValid = HEADER_PATTERN.test(header)

          return [
            isValid,
            'commit must match: <type>(<scope>)?: <PROJ-123> <english description>',
          ]
        },
      },
    },
  ],
  rules: {
    'type-enum': [2, 'always', ALLOWED_TYPES],
    'subject-empty': [2, 'never'],
    'subject-case': [0],
    'jira-ticket-required': [2, 'always'],
  },
}
