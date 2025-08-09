/// <reference types="vitest/globals" />

import { vi } from "vitest";

declare global {
  var vi: typeof vi;
  var expect: typeof import("vitest").expect;
  var describe: typeof import("vitest").describe;
  var it: typeof import("vitest").it;
  var test: typeof import("vitest").test;
  var beforeAll: typeof import("vitest").beforeAll;
  var afterAll: typeof import("vitest").afterAll;
  var beforeEach: typeof import("vitest").beforeEach;
  var afterEach: typeof import("vitest").afterEach;
}
