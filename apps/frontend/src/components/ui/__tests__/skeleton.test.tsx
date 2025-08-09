/**
 * Skeleton Component Tests
 *
 * Following CLAUDE.md testing directives:
 * - NEVER mock internal frontend code, components, hooks, or utilities
 * - ONLY mock external APIs (third-party services, etc.)
 * - Test actual behavior, not implementation details
 */

import { render } from "@testing-library/react";
import { describe, it, expect } from "vitest";
import { Skeleton } from "../skeleton";

describe("Skeleton Component", () => {
  describe("Basic Rendering", () => {
    it("should render skeleton with default styling", () => {
      const { container } = render(<Skeleton />);
      
      const skeletonElement = container.firstChild as HTMLElement;
      expect(skeletonElement).toBeInTheDocument();
      expect(skeletonElement).toHaveClass("animate-pulse");
      expect(skeletonElement).toHaveClass("rounded-md");
      expect(skeletonElement).toHaveClass("bg-muted");
    });
    
    it("should apply custom className", () => {
      const { container } = render(<Skeleton className="custom-skeleton w-full h-4" />);
      
      const skeletonElement = container.firstChild as HTMLElement;
      expect(skeletonElement).toHaveClass("custom-skeleton");
      expect(skeletonElement).toHaveClass("w-full");
      expect(skeletonElement).toHaveClass("h-4");
    });
    
    it("should render as a div element by default", () => {
      const { container } = render(<Skeleton />);
      
      const skeletonElement = container.firstChild as HTMLElement;
      expect(skeletonElement.tagName).toBe("DIV");
    });
  });
  
  describe("Size Variations", () => {
    it("should render with small size classes", () => {
      const { container } = render(<Skeleton className="h-2 w-16" />);
      
      const skeletonElement = container.firstChild as HTMLElement;
      expect(skeletonElement).toHaveClass("h-2");
      expect(skeletonElement).toHaveClass("w-16");
    });
    
    it("should render with large size classes", () => {
      const { container } = render(<Skeleton className="h-12 w-full" />);
      
      const skeletonElement = container.firstChild as HTMLElement;
      expect(skeletonElement).toHaveClass("h-12");
      expect(skeletonElement).toHaveClass("w-full");
    });
    
    it("should support circular skeleton", () => {
      const { container } = render(<Skeleton className="h-10 w-10 rounded-full" />);
      
      const skeletonElement = container.firstChild as HTMLElement;
      expect(skeletonElement).toHaveClass("rounded-full");
      expect(skeletonElement).toHaveClass("h-10");
      expect(skeletonElement).toHaveClass("w-10");
    });
  });
  
  describe("Multiple Skeleton Pattern", () => {
    it("should render multiple skeletons in a container", () => {
      const { container } = render(
        <div className="space-y-2">
          <Skeleton className="h-4 w-full" />
          <Skeleton className="h-4 w-3/4" />
          <Skeleton className="h-4 w-1/2" />
        </div>
      );
      
      const skeletonElements = container.querySelectorAll(".animate-pulse");
      expect(skeletonElements).toHaveLength(3);
      
      expect(skeletonElements[0]).toHaveClass("w-full");
      expect(skeletonElements[1]).toHaveClass("w-3/4");
      expect(skeletonElements[2]).toHaveClass("w-1/2");
    });
  });
  
  describe("Common Loading Patterns", () => {
    it("should render text skeleton pattern", () => {
      const { container } = render(
        <div className="space-y-2">
          <Skeleton className="h-6 w-48" />
          <Skeleton className="h-4 w-full" />
          <Skeleton className="h-4 w-full" />
          <Skeleton className="h-4 w-2/3" />
        </div>
      );
      
      const skeletons = container.querySelectorAll(".animate-pulse");
      expect(skeletons).toHaveLength(4);
      
      // Title skeleton
      expect(skeletons[0]).toHaveClass("h-6");
      expect(skeletons[0]).toHaveClass("w-48");
      
      // Content skeletons
      expect(skeletons[1]).toHaveClass("h-4");
      expect(skeletons[2]).toHaveClass("h-4");
      expect(skeletons[3]).toHaveClass("w-2/3");
    });
    
    it("should render avatar skeleton pattern", () => {
      const { container } = render(
        <div className="flex items-center space-x-4">
          <Skeleton className="h-12 w-12 rounded-full" />
          <div className="space-y-2">
            <Skeleton className="h-4 w-32" />
            <Skeleton className="h-3 w-24" />
          </div>
        </div>
      );
      
      const skeletons = container.querySelectorAll(".animate-pulse");
      expect(skeletons).toHaveLength(3);
      
      // Avatar skeleton
      expect(skeletons[0]).toHaveClass("rounded-full");
      expect(skeletons[0]).toHaveClass("h-12");
      expect(skeletons[0]).toHaveClass("w-12");
    });
    
    it("should render card skeleton pattern", () => {
      const { container } = render(
        <div className="space-y-4">
          <div className="space-y-2">
            <Skeleton className="h-32 w-full" />
            <Skeleton className="h-6 w-3/4" />
            <Skeleton className="h-4 w-full" />
            <Skeleton className="h-4 w-full" />
            <Skeleton className="h-4 w-1/2" />
          </div>
        </div>
      );
      
      const skeletons = container.querySelectorAll(".animate-pulse");
      expect(skeletons).toHaveLength(5);
      
      // Image skeleton
      expect(skeletons[0]).toHaveClass("h-32");
      
      // Title skeleton
      expect(skeletons[1]).toHaveClass("h-6");
      
      // Content skeletons
      expect(skeletons[2]).toHaveClass("h-4");
      expect(skeletons[3]).toHaveClass("h-4");
      expect(skeletons[4]).toHaveClass("w-1/2");
    });
  });
  
  describe("Table Skeleton Pattern", () => {
    it("should render table skeleton with rows and columns", () => {
      const { container } = render(
        <div className="space-y-2">
          {/* Header row */}
          <div className="flex space-x-4">
            <Skeleton className="h-4 w-24" />
            <Skeleton className="h-4 w-32" />
            <Skeleton className="h-4 w-20" />
            <Skeleton className="h-4 w-16" />
          </div>
          
          {/* Data rows */}
          {Array.from({ length: 3 }).map((_, i) => (
            <div key={i} className="flex space-x-4">
              <Skeleton className="h-4 w-24" />
              <Skeleton className="h-4 w-32" />
              <Skeleton className="h-4 w-20" />
              <Skeleton className="h-4 w-16" />
            </div>
          ))}
        </div>
      );
      
      const skeletons = container.querySelectorAll(".animate-pulse");
      // Header (4) + 3 rows × 4 columns = 16 total
      expect(skeletons).toHaveLength(16);
    });
  });
  
  describe("Animation and Styling", () => {
    it("should have pulse animation by default", () => {
      const { container } = render(<Skeleton />);
      
      const skeletonElement = container.firstChild as HTMLElement;
      expect(skeletonElement).toHaveClass("animate-pulse");
    });
    
    it("should support custom animation classes", () => {
      const { container } = render(
        <Skeleton className="animate-bounce bg-gray-300" />
      );
      
      const skeletonElement = container.firstChild as HTMLElement;
      // Should still have pulse (from component) and bounce (custom)
      expect(skeletonElement).toHaveClass("animate-pulse");
      expect(skeletonElement).toHaveClass("animate-bounce");
      expect(skeletonElement).toHaveClass("bg-gray-300");
    });
    
    it("should support different background colors", () => {
      const { container } = render(
        <Skeleton className="bg-slate-200" />
      );
      
      const skeletonElement = container.firstChild as HTMLElement;
      expect(skeletonElement).toHaveClass("bg-slate-200");
    });
  });
  
  describe("Accessibility", () => {
    it("should be accessible with proper loading indication", () => {
      const { container } = render(
        <Skeleton aria-label="Carregando conteúdo..." role="status" />
      );
      
      const skeletonElement = container.firstChild as HTMLElement;
      expect(skeletonElement).toHaveAttribute("aria-label", "Carregando conteúdo...");
      expect(skeletonElement).toHaveAttribute("role", "status");
    });
    
    it("should support screen reader text", () => {
      const { container } = render(
        <Skeleton>
          <span className="sr-only">Carregando dados do usuário...</span>
        </Skeleton>
      );
      
      const screenReaderText = container.querySelector(".sr-only");
      expect(screenReaderText).toBeInTheDocument();
      expect(screenReaderText).toHaveTextContent("Carregando dados do usuário...");
    });
  });
});