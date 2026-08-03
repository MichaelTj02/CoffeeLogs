const nextJest = require("next/jest");

const createJestConfig = nextJest({ dir: "./" });

module.exports = createJestConfig({
  testEnvironment: "jest-environment-jsdom",
  setupFilesAfterEnv: ["<rootDir>/jest.setup.js"],
  // SWC rewrites the jsconfig `@/*` alias in import statements, but not in the string
  // argument to jest.mock, which resolves through Jest's own mapper.
  moduleNameMapper: { "^@/(.*)$": "<rootDir>/$1" },
});
