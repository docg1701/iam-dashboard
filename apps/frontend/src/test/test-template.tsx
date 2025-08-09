/**
 * Universal Test Template with External API Mocks Only
 *
 * Following CLAUDE.md testing directives:
 * - NEVER mock internal frontend code, components, hooks, or utilities
 * - ONLY mock external APIs (fetch, browser APIs, third-party services)
 * - Use real component rendering and actual data flows
 * - Test actual behavior, not implementation details
 */

import { render, type RenderOptions, act } from "@testing-library/react";
import { QueryClientProvider, QueryClient } from "@tanstack/react-query";
import { vi, beforeEach, afterEach } from "vitest";
import { createTestQueryClient } from "./query-client";
import { clearTestAuth } from "./auth-helpers";
import { ToastProvider } from "@/components/ui/toast";

// Import our enhanced setup with smart fetch mocking
import "./setup";

// ============================================================================
// External Framework Mocks (Next.js, etc.)
// ============================================================================

// Next.js Navigation mock (external framework - safe to mock)
vi.mock("next/navigation", () => ({
  useRouter: () => ({
    push: vi.fn(),
    replace: vi.fn(),
    prefetch: vi.fn(),
    back: vi.fn(),
    forward: vi.fn(),
    refresh: vi.fn(),
  }),
  usePathname: () => "/test-path",
  useSearchParams: () => new URLSearchParams(),
  notFound: vi.fn(),
  redirect: vi.fn(),
}));

// ============================================================================
// External Browser API Mocks (External Dependencies Only)
// ============================================================================

/**
 * Setup external browser API mocks
 * These are external to our application and safe to mock
 */
const setupExternalBrowserMocks = () => {
  // ResizeObserver (external browser API)
  global.ResizeObserver = vi.fn(() => ({
    observe: vi.fn(),
    unobserve: vi.fn(),
    disconnect: vi.fn(),
  }));

  // IntersectionObserver (external browser API)
  (global as any).IntersectionObserver = vi.fn(() => ({
    observe: vi.fn(),
    unobserve: vi.fn(),
    disconnect: vi.fn(),
    takeRecords: vi.fn(() => []),
    root: null,
    rootMargin: "",
    thresholds: [],
  }));

  // matchMedia (external browser API)
  Object.defineProperty(window, "matchMedia", {
    writable: true,
    value: vi.fn().mockImplementation((query) => ({
      matches: false,
      media: query,
      onchange: null,
      addListener: vi.fn(),
      removeListener: vi.fn(),
      addEventListener: vi.fn(),
      removeEventListener: vi.fn(),
      dispatchEvent: vi.fn(),
    })),
  });

  // localStorage mock (external browser API)
  Object.defineProperty(window, "localStorage", {
    value: {
      getItem: vi.fn(() => null),
      setItem: vi.fn(),
      removeItem: vi.fn(),
      clear: vi.fn(),
      length: 0,
      key: vi.fn(),
    },
    writable: true,
  });

  // sessionStorage mock (external browser API)
  Object.defineProperty(window, "sessionStorage", {
    value: {
      getItem: vi.fn(() => null),
      setItem: vi.fn(),
      removeItem: vi.fn(),
      clear: vi.fn(),
      length: 0,
      key: vi.fn(),
    },
    writable: true,
  });

  // Location mock (external browser API)
  delete (window as any).location;
  window.location = {
    assign: vi.fn(),
    href: "http://localhost:3000",
    origin: "http://localhost:3000",
    protocol: "http:",
    host: "localhost:3000",
    hostname: "localhost",
    port: "3000",
    pathname: "/",
    search: "",
    hash: "",
    replace: vi.fn(),
    reload: vi.fn(),
    toString: () => "http://localhost:3000",
  } as any;

  // History API mock (external browser API)
  Object.defineProperty(window, "history", {
    value: {
      pushState: vi.fn(),
      replaceState: vi.fn(),
      back: vi.fn(),
      forward: vi.fn(),
      go: vi.fn(),
      length: 1,
      state: null,
    },
    writable: true,
  });

  // Navigator mock (external browser API)
  Object.defineProperty(window, "navigator", {
    value: {
      userAgent: "Mozilla/5.0 (Test Environment)",
      language: "en-US",
      languages: ["en-US", "en"],
      platform: "Test",
      cookieEnabled: true,
      onLine: true,
      clipboard: {
        writeText: vi.fn(() => Promise.resolve()),
        readText: vi.fn(() => Promise.resolve("")),
      },
    },
    writable: true,
  });

  // Console mock to suppress expected warnings
  const originalConsole = { ...console };
  console.warn = vi.fn();
  console.error = vi.fn();

  return originalConsole;
};

/**
 * Setup DOM element mocks for layout calculations
 */
const setupDOMElementMocks = () => {
  // Mock getBoundingClientRect for layout calculations
  Element.prototype.getBoundingClientRect = vi.fn(() => ({
    x: 0,
    y: 0,
    top: 0,
    left: 0,
    bottom: 100,
    right: 100,
    width: 100,
    height: 100,
    toJSON: vi.fn(),
  }));

  // Mock scroll methods
  Element.prototype.scrollTo = vi.fn();
  Element.prototype.scrollIntoView = vi.fn();
  window.scrollTo = vi.fn();

  // Mock pointer capture methods for Radix UI
  Element.prototype.hasPointerCapture = vi.fn(() => false);
  Element.prototype.setPointerCapture = vi.fn();
  Element.prototype.releasePointerCapture = vi.fn();

  // Mock getComputedStyle
  window.getComputedStyle = vi.fn(() => ({
    getPropertyValue: vi.fn(() => ""),
    display: "block",
    visibility: "visible",
    opacity: "1",
    position: "static",
    zIndex: "auto",
  })) as any;

  // Mock CSS support queries
  CSS.supports = vi.fn(() => true);
};

/**
 * Setup WebSocket mock (external service)
 */
const setupWebSocketMock = () => {
  global.WebSocket = vi.fn().mockImplementation((url) => ({
    url,
    readyState: 1, // OPEN
    CONNECTING: 0,
    OPEN: 1,
    CLOSING: 2,
    CLOSED: 3,
    close: vi.fn(),
    send: vi.fn(),
    addEventListener: vi.fn(),
    removeEventListener: vi.fn(),
    dispatchEvent: vi.fn(),
    onopen: null,
    onclose: null,
    onmessage: null,
    onerror: null,
    bufferedAmount: 0,
    extensions: "",
    protocol: "",
    binaryType: "blob",
  })) as any;
};

// ============================================================================
// Test Wrapper Components
// ============================================================================

/**
 * Test wrapper with all necessary providers
 * Uses real providers - never mocks internal components
 */
interface TestWrapperProps {
  children: React.ReactNode;
  queryClient?: QueryClient;
}

export const TestWrapper = ({ children, queryClient }: TestWrapperProps) => {
  const client = queryClient || createTestQueryClient();

  return (
    <QueryClientProvider client={client}>
      <ToastProvider>{children}</ToastProvider>
    </QueryClientProvider>
  );
};

/**
 * Custom render function with providers
 * Follows React Testing Library best practices
 */
interface CustomRenderOptions extends Omit<RenderOptions, "wrapper"> {
  wrapper?: React.ComponentType<any>;
  queryClient?: QueryClient;
}

export const renderWithProviders = (
  ui: React.ReactElement,
  options: CustomRenderOptions = {},
) => {
  const { wrapper, queryClient, ...renderOptions } = options;

  const Wrapper =
    wrapper ||
    (({ children }: { children: React.ReactNode }) => (
      <TestWrapper queryClient={queryClient}>{children}</TestWrapper>
    ));

  return render(ui, { ...renderOptions, wrapper: Wrapper });
};

// ============================================================================
// Standard Test Setup Hook
// ============================================================================

/**
 * Standard test setup hook
 * Call this in describe blocks to set up consistent test environment
 */
export const useTestSetup = () => {
  let originalConsole: any;

  beforeEach(() => {
    // Clear all mocks from previous tests
    vi.clearAllMocks();

    // Clear auth state to start fresh
    clearTestAuth();

    // Setup external browser mocks
    originalConsole = setupExternalBrowserMocks();
    setupDOMElementMocks();
    setupWebSocketMock();
  });

  afterEach(() => {
    // Restore all mocks
    vi.restoreAllMocks();

    // Clear auth state after test
    clearTestAuth();

    // Restore console
    if (originalConsole) {
      console.warn = originalConsole.warn;
      console.error = originalConsole.error;
    }
  });
};

// ============================================================================
// Advanced Test Utilities
// ============================================================================

/**
 * Wait for async operations to complete
 * Useful for testing async state updates
 */
export const waitForAsyncUpdates = () =>
  new Promise((resolve) => setTimeout(resolve, 0));

/**
 * Enhanced act wrapper that handles multiple async updates
 * Specifically for shadcn/ui components like Select that trigger multiple state updates
 */
export const actWithMultipleUpdates = async (
  fn: () => Promise<void> | void,
) => {
  await act(async () => {
    await fn();
    // Wait for additional state updates from shadcn components
    await waitForAsyncUpdates();
  });
  // Additional wait for DOM updates to settle
  await waitForAsyncUpdates();
};

/**
 * Trigger window resize event for responsive testing
 */
export const triggerWindowResize = (
  width: number = 1024,
  height: number = 768,
) => {
  Object.defineProperty(window, "innerWidth", {
    writable: true,
    configurable: true,
    value: width,
  });
  Object.defineProperty(window, "innerHeight", {
    writable: true,
    configurable: true,
    value: height,
  });

  const event = new Event("resize");
  window.dispatchEvent(event);
};

/**
 * Mock successful fetch response for specific endpoint
 */
export const mockSuccessfulFetch = (
  endpoint: string,
  responseData: any,
  status: number = 200,
) => {
  vi.mocked(global.fetch).mockImplementationOnce((url) => {
    if (url.toString().includes(endpoint)) {
      return Promise.resolve({
        ok: true,
        status,
        statusText: "OK",
        json: () => Promise.resolve(responseData),
        text: () => Promise.resolve(JSON.stringify(responseData)),
        headers: new Headers({ "content-type": "application/json" }),
        clone: function () {
          return this;
        },
        body: null,
        bodyUsed: false,
        arrayBuffer: () => Promise.resolve(new ArrayBuffer(0)),
        blob: () => Promise.resolve(new Blob()),
        formData: () => Promise.resolve(new FormData()),
      } as Response);
    }

    // Fall back to default mock behavior
    return global.fetch(url as any);
  });
};

/**
 * Mock failed fetch response for testing error scenarios
 */
export const mockFailedFetch = (
  endpoint: string,
  error: string,
  status: number = 500,
) => {
  vi.mocked(global.fetch).mockImplementationOnce((url) => {
    if (url.toString().includes(endpoint)) {
      return Promise.resolve({
        ok: false,
        status,
        statusText: "Internal Server Error",
        json: () => Promise.resolve({ error, detail: error }),
        text: () => Promise.resolve(JSON.stringify({ error, detail: error })),
        headers: new Headers({ "content-type": "application/json" }),
        clone: function () {
          return this;
        },
        body: null,
        bodyUsed: false,
        arrayBuffer: () => Promise.resolve(new ArrayBuffer(0)),
        blob: () => Promise.resolve(new Blob()),
        formData: () => Promise.resolve(new FormData()),
      } as Response);
    }

    // Fall back to default mock behavior
    return global.fetch(url as any);
  });
};

/**
 * Mock network error for testing offline scenarios
 */
export const mockNetworkError = (
  endpoint: string,
  errorMessage: string = "Network error",
) => {
  vi.mocked(global.fetch).mockImplementationOnce((url) => {
    if (url.toString().includes(endpoint)) {
      return Promise.reject(new Error(errorMessage));
    }

    // Fall back to default mock behavior
    return global.fetch(url as any);
  });
};

/**
 * Mock multiple sequential fetch responses for complex flows
 * Useful for testing login + 2FA verification flows
 */
export const mockSequentialFetch = (
  ...mocks: Array<{ endpoint: string; responseData: any; status?: number }>
) => {
  let callCount = 0;

  vi.mocked(global.fetch).mockImplementation((url) => {
    const urlStr = url.toString();

    for (const mock of mocks) {
      if (urlStr.includes(mock.endpoint)) {
        const response = {
          ok: (mock.status || 200) < 400,
          status: mock.status || 200,
          statusText: (mock.status || 200) < 400 ? "OK" : "Error",
          json: () => Promise.resolve(mock.responseData),
          text: () => Promise.resolve(JSON.stringify(mock.responseData)),
          headers: new Headers({ "content-type": "application/json" }),
          clone: function () {
            return this;
          },
          body: null,
          bodyUsed: false,
          arrayBuffer: () => Promise.resolve(new ArrayBuffer(0)),
          blob: () => Promise.resolve(new Blob()),
          formData: () => Promise.resolve(new FormData()),
        } as Response;

        // Remove this mock after use to allow for sequential calls
        mocks.splice(mocks.indexOf(mock), 1);

        return Promise.resolve(response);
      }
    }

    // Fall back to default mock behavior
    return global.fetch(url as any);
  });
};

// ============================================================================
// Re-export commonly used testing utilities
// ============================================================================

// React Testing Library exports
export {
  screen,
  waitFor,
  fireEvent,
  act,
  cleanup,
  within,
  getByRole,
  getByText,
  getByLabelText,
  getByTestId,
  queryByRole,
  queryByText,
  queryByLabelText,
  queryByTestId,
  findByRole,
  findByText,
  findByLabelText,
  findByTestId,
} from "@testing-library/react";

// User Event for interactions
export { userEvent } from "@testing-library/user-event";

// Vitest exports
export {
  vi,
  describe,
  it,
  test,
  expect,
  beforeEach,
  afterEach,
  beforeAll,
  afterAll,
  suite,
} from "vitest";

// Jest DOM matchers
import "@testing-library/jest-dom";

export default {
  // Core render utilities
  renderWithProviders,
  TestWrapper,
  useTestSetup,

  // Advanced utilities
  waitForAsyncUpdates,
  actWithMultipleUpdates,
  triggerWindowResize,
  mockSuccessfulFetch,
  mockFailedFetch,
  mockNetworkError,
  mockSequentialFetch,
};
