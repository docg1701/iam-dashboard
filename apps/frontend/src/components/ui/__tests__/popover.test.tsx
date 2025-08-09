/**
 * Popover Component Tests
 *
 * Following CLAUDE.md testing directives:
 * - NEVER mock internal frontend code, components, hooks, or utilities
 * - ONLY mock external APIs (third-party services, etc.)
 * - Test actual behavior, not implementation details
 */

import React from "react";
import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import { describe, it, expect, vi } from "vitest";
import { Popover, PopoverTrigger, PopoverContent } from "../popover";

describe("Popover Components", () => {
  describe("Basic Popover", () => {
    it("should render popover trigger", () => {
      render(
        <Popover>
          <PopoverTrigger asChild>
            <button>Open Popover</button>
          </PopoverTrigger>
          <PopoverContent>
            <div>Popover Content</div>
          </PopoverContent>
        </Popover>
      );
      
      const trigger = screen.getByRole("button", { name: "Open Popover" });
      expect(trigger).toBeInTheDocument();
    });
    
    it("should open popover when trigger is clicked", async () => {
      render(
        <Popover>
          <PopoverTrigger asChild>
            <button>Open Popover</button>
          </PopoverTrigger>
          <PopoverContent>
            <div>Popover Content</div>
          </PopoverContent>
        </Popover>
      );
      
      const trigger = screen.getByRole("button", { name: "Open Popover" });
      fireEvent.click(trigger);
      
      await waitFor(() => {
        expect(screen.getByText("Popover Content")).toBeVisible();
      });
    });
    
    it("should close popover when clicking outside", async () => {
      render(
        <div>
          <div data-testid="outside">Outside</div>
          <Popover>
            <PopoverTrigger asChild>
              <button>Open Popover</button>
            </PopoverTrigger>
            <PopoverContent>
              <div>Popover Content</div>
            </PopoverContent>
          </Popover>
        </div>
      );
      
      const trigger = screen.getByRole("button", { name: "Open Popover" });
      fireEvent.click(trigger);
      
      await waitFor(() => {
        expect(screen.getByText("Popover Content")).toBeVisible();
      });
      
      // Click outside
      fireEvent.click(screen.getByTestId("outside"));
      
      await waitFor(() => {
        expect(screen.queryByText("Popover Content")).not.toBeVisible();
      });
    });
  });
  
  describe("Controlled Popover", () => {
    it("should work in controlled mode", async () => {
      const onOpenChange = vi.fn();
      
      const ControlledPopover = () => {
        const [open, setOpen] = React.useState(false);
        
        return (
          <Popover 
            open={open} 
            onOpenChange={(isOpen) => {
              setOpen(isOpen);
              onOpenChange(isOpen);
            }}
          >
            <PopoverTrigger asChild>
              <button>Controlled Trigger</button>
            </PopoverTrigger>
            <PopoverContent>
              <div>Controlled Content</div>
            </PopoverContent>
          </Popover>
        );
      };
      
      render(<ControlledPopover />);
      
      const trigger = screen.getByRole("button", { name: "Controlled Trigger" });
      fireEvent.click(trigger);
      
      expect(onOpenChange).toHaveBeenCalledWith(true);
      
      await waitFor(() => {
        expect(screen.getByText("Controlled Content")).toBeVisible();
      });
    });
  });
  
  describe("Popover Content", () => {
    it("should render complex content", async () => {
      render(
        <Popover>
          <PopoverTrigger asChild>
            <button>Open</button>
          </PopoverTrigger>
          <PopoverContent>
            <div className="space-y-2">
              <h3>Popover Title</h3>
              <p>This is popover description.</p>
              <button>Action Button</button>
            </div>
          </PopoverContent>
        </Popover>
      );
      
      fireEvent.click(screen.getByRole("button", { name: "Open" }));
      
      await waitFor(() => {
        expect(screen.getByText("Popover Title")).toBeInTheDocument();
        expect(screen.getByText("This is popover description.")).toBeInTheDocument();
        expect(screen.getByRole("button", { name: "Action Button" })).toBeInTheDocument();
      });
    });
    
    it("should handle interactive content", async () => {
      const onButtonClick = vi.fn();
      
      render(
        <Popover>
          <PopoverTrigger asChild>
            <button>Open</button>
          </PopoverTrigger>
          <PopoverContent>
            <button onClick={onButtonClick}>Interactive Button</button>
          </PopoverContent>
        </Popover>
      );
      
      fireEvent.click(screen.getByRole("button", { name: "Open" }));
      
      await waitFor(() => {
        const interactiveButton = screen.getByRole("button", { name: "Interactive Button" });
        expect(interactiveButton).toBeInTheDocument();
        
        fireEvent.click(interactiveButton);
        expect(onButtonClick).toHaveBeenCalled();
      });
    });
    
    it("should support form elements", async () => {
      const onSubmit = vi.fn((e) => e.preventDefault());
      
      render(
        <Popover>
          <PopoverTrigger asChild>
            <button>Open Form</button>
          </PopoverTrigger>
          <PopoverContent>
            <form onSubmit={onSubmit}>
              <input placeholder="Enter text" />
              <button type="submit">Submit</button>
            </form>
          </PopoverContent>
        </Popover>
      );
      
      fireEvent.click(screen.getByRole("button", { name: "Open Form" }));
      
      await waitFor(() => {
        const input = screen.getByPlaceholderText("Enter text");
        const submitBtn = screen.getByRole("button", { name: "Submit" });
        
        expect(input).toBeInTheDocument();
        expect(submitBtn).toBeInTheDocument();
        
        fireEvent.change(input, { target: { value: "test value" } });
        fireEvent.click(submitBtn);
        
        expect(onSubmit).toHaveBeenCalled();
      });
    });
  });
  
  describe("Positioning and Alignment", () => {
    it("should support different alignment options", async () => {
      render(
        <Popover>
          <PopoverTrigger asChild>
            <button>Open</button>
          </PopoverTrigger>
          <PopoverContent align="start">
            <div>Left Aligned Content</div>
          </PopoverContent>
        </Popover>
      );
      
      fireEvent.click(screen.getByRole("button", { name: "Open" }));
      
      await waitFor(() => {
        expect(screen.getByText("Left Aligned Content")).toBeVisible();
      });
    });
    
    it("should support different side options", async () => {
      render(
        <Popover>
          <PopoverTrigger asChild>
            <button>Open</button>
          </PopoverTrigger>
          <PopoverContent side="top">
            <div>Top Positioned Content</div>
          </PopoverContent>
        </Popover>
      );
      
      fireEvent.click(screen.getByRole("button", { name: "Open" }));
      
      await waitFor(() => {
        expect(screen.getByText("Top Positioned Content")).toBeVisible();
      });
    });
    
    it("should support alignment offset", async () => {
      render(
        <Popover>
          <PopoverTrigger asChild>
            <button>Open</button>
          </PopoverTrigger>
          <PopoverContent alignOffset={10}>
            <div>Offset Content</div>
          </PopoverContent>
        </Popover>
      );
      
      fireEvent.click(screen.getByRole("button", { name: "Open" }));
      
      await waitFor(() => {
        expect(screen.getByText("Offset Content")).toBeVisible();
      });
    });
  });
  
  describe("Keyboard Navigation", () => {
    it("should open with Enter key", async () => {
      render(
        <Popover>
          <PopoverTrigger asChild>
            <button>Keyboard Trigger</button>
          </PopoverTrigger>
          <PopoverContent>
            <div>Keyboard Content</div>
          </PopoverContent>
        </Popover>
      );
      
      const trigger = screen.getByRole("button", { name: "Keyboard Trigger" });
      trigger.focus();
      
      fireEvent.keyDown(trigger, { key: "Enter" });
      
      await waitFor(() => {
        expect(screen.getByText("Keyboard Content")).toBeVisible();
      });
    });
    
    it("should open with Space key", async () => {
      render(
        <Popover>
          <PopoverTrigger asChild>
            <button>Space Trigger</button>
          </PopoverTrigger>
          <PopoverContent>
            <div>Space Content</div>
          </PopoverContent>
        </Popover>
      );
      
      const trigger = screen.getByRole("button", { name: "Space Trigger" });
      trigger.focus();
      
      fireEvent.keyDown(trigger, { key: " " });
      
      await waitFor(() => {
        expect(screen.getByText("Space Content")).toBeVisible();
      });
    });
    
    it("should close with Escape key", async () => {
      render(
        <Popover>
          <PopoverTrigger asChild>
            <button>Escape Test</button>
          </PopoverTrigger>
          <PopoverContent>
            <div>Escape Content</div>
          </PopoverContent>
        </Popover>
      );
      
      fireEvent.click(screen.getByRole("button", { name: "Escape Test" }));
      
      await waitFor(() => {
        expect(screen.getByText("Escape Content")).toBeVisible();
      });
      
      fireEvent.keyDown(document, { key: "Escape" });
      
      await waitFor(() => {
        expect(screen.queryByText("Escape Content")).not.toBeVisible();
      });
    });
  });
  
  describe("Custom Styling", () => {
    it("should apply custom className to trigger", () => {
      const { container } = render(
        <Popover>
          <PopoverTrigger className="custom-trigger" asChild>
            <button>Custom Trigger</button>
          </PopoverTrigger>
          <PopoverContent>
            <div>Content</div>
          </PopoverContent>
        </Popover>
      );
      
      const customTrigger = container.querySelector(".custom-trigger");
      expect(customTrigger).toBeInTheDocument();
    });
    
    it("should apply custom className to content", async () => {
      const { container } = render(
        <Popover>
          <PopoverTrigger asChild>
            <button>Trigger</button>
          </PopoverTrigger>
          <PopoverContent className="custom-content">
            <div>Custom Content</div>
          </PopoverContent>
        </Popover>
      );
      
      fireEvent.click(screen.getByRole("button", { name: "Trigger" }));
      
      await waitFor(() => {
        const customContent = container.querySelector(".custom-content");
        expect(customContent).toBeInTheDocument();
      });
    });
  });
  
  describe("Accessibility", () => {
    it("should have proper ARIA attributes", async () => {
      render(
        <Popover>
          <PopoverTrigger asChild>
            <button>ARIA Trigger</button>
          </PopoverTrigger>
          <PopoverContent>
            <div>ARIA Content</div>
          </PopoverContent>
        </Popover>
      );
      
      const trigger = screen.getByRole("button", { name: "ARIA Trigger" });
      
      // Check initial ARIA state
      expect(trigger).toHaveAttribute("aria-expanded", "false");
      
      fireEvent.click(trigger);
      
      await waitFor(() => {
        expect(trigger).toHaveAttribute("aria-expanded", "true");
        
        // Content should be accessible
        const content = screen.getByText("ARIA Content");
        expect(content).toBeInTheDocument();
      });
    });
    
    it("should support custom ARIA labels", async () => {
      render(
        <Popover>
          <PopoverTrigger aria-label="Custom popover trigger" asChild>
            <button>🔍</button>
          </PopoverTrigger>
          <PopoverContent>
            <div>Search Options</div>
          </PopoverContent>
        </Popover>
      );
      
      const trigger = screen.getByRole("button", { name: "Custom popover trigger" });
      expect(trigger).toBeInTheDocument();
      
      fireEvent.click(trigger);
      
      await waitFor(() => {
        expect(screen.getByText("Search Options")).toBeVisible();
      });
    });
  });
  
  describe("Portal Behavior", () => {
    it("should render content in portal", async () => {
      render(
        <div data-testid="app-root">
          <Popover>
            <PopoverTrigger asChild>
              <button>Portal Test</button>
            </PopoverTrigger>
            <PopoverContent>
              <div>Portal Content</div>
            </PopoverContent>
          </Popover>
        </div>
      );
      
      fireEvent.click(screen.getByRole("button", { name: "Portal Test" }));
      
      await waitFor(() => {
        const content = screen.getByText("Portal Content");
        expect(content).toBeInTheDocument();
        
        // Content should be rendered outside the app root
        const appRoot = screen.getByTestId("app-root");
        expect(appRoot).not.toContainElement(content);
      });
    });
  });
});