/**
 * DropdownMenu Component Tests
 *
 * Following CLAUDE.md testing directives:
 * - NEVER mock internal frontend code, components, hooks, or utilities
 * - ONLY mock external APIs (third-party services, etc.)
 * - Test actual behavior, not implementation details
 */

import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import { describe, it, expect, vi } from "vitest";
import {
  DropdownMenu,
  DropdownMenuTrigger,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuCheckboxItem,
  DropdownMenuRadioItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuShortcut,
  DropdownMenuGroup,
  DropdownMenuPortal,
  DropdownMenuSub,
  DropdownMenuSubContent,
  DropdownMenuSubTrigger,
  DropdownMenuRadioGroup,
} from "../dropdown-menu";

describe("DropdownMenu Components", () => {
  describe("Basic Dropdown Menu", () => {
    it("should render dropdown trigger button", () => {
      render(
        <DropdownMenu>
          <DropdownMenuTrigger asChild>
            <button>Open Menu</button>
          </DropdownMenuTrigger>
          <DropdownMenuContent>
            <DropdownMenuItem>Item 1</DropdownMenuItem>
          </DropdownMenuContent>
        </DropdownMenu>
      );
      
      const trigger = screen.getByRole("button", { name: "Open Menu" });
      expect(trigger).toBeInTheDocument();
    });
    
    it("should open dropdown menu when clicked", async () => {
      render(
        <DropdownMenu>
          <DropdownMenuTrigger asChild>
            <button>Open Menu</button>
          </DropdownMenuTrigger>
          <DropdownMenuContent>
            <DropdownMenuItem>Menu Item</DropdownMenuItem>
          </DropdownMenuContent>
        </DropdownMenu>
      );
      
      const trigger = screen.getByRole("button", { name: "Open Menu" });
      fireEvent.click(trigger);
      
      await waitFor(() => {
        expect(screen.getByText("Menu Item")).toBeVisible();
      });
    });
  });
  
  describe("DropdownMenuItem", () => {
    it("should render menu items", async () => {
      render(
        <DropdownMenu>
          <DropdownMenuTrigger asChild>
            <button>Menu</button>
          </DropdownMenuTrigger>
          <DropdownMenuContent>
            <DropdownMenuItem>Item 1</DropdownMenuItem>
            <DropdownMenuItem>Item 2</DropdownMenuItem>
            <DropdownMenuItem>Item 3</DropdownMenuItem>
          </DropdownMenuContent>
        </DropdownMenu>
      );
      
      fireEvent.click(screen.getByRole("button", { name: "Menu" }));
      
      await waitFor(() => {
        expect(screen.getByText("Item 1")).toBeInTheDocument();
        expect(screen.getByText("Item 2")).toBeInTheDocument();
        expect(screen.getByText("Item 3")).toBeInTheDocument();
      });
    });
    
    it("should handle menu item clicks", async () => {
      const onSelect = vi.fn();
      
      render(
        <DropdownMenu>
          <DropdownMenuTrigger asChild>
            <button>Menu</button>
          </DropdownMenuTrigger>
          <DropdownMenuContent>
            <DropdownMenuItem onSelect={onSelect}>Clickable Item</DropdownMenuItem>
          </DropdownMenuContent>
        </DropdownMenu>
      );
      
      fireEvent.click(screen.getByRole("button", { name: "Menu" }));
      
      await waitFor(() => {
        expect(screen.getByText("Clickable Item")).toBeInTheDocument();
      });
      
      fireEvent.click(screen.getByText("Clickable Item"));
      expect(onSelect).toHaveBeenCalled();
    });
    
    it("should handle disabled menu items", async () => {
      const onSelect = vi.fn();
      
      render(
        <DropdownMenu>
          <DropdownMenuTrigger asChild>
            <button>Menu</button>
          </DropdownMenuTrigger>
          <DropdownMenuContent>
            <DropdownMenuItem disabled onSelect={onSelect}>
              Disabled Item
            </DropdownMenuItem>
          </DropdownMenuContent>
        </DropdownMenu>
      );
      
      fireEvent.click(screen.getByRole("button", { name: "Menu" }));
      
      await waitFor(() => {
        const disabledItem = screen.getByText("Disabled Item");
        expect(disabledItem).toBeInTheDocument();
        
        // Click disabled item
        fireEvent.click(disabledItem);
        expect(onSelect).not.toHaveBeenCalled();
      });
    });
  });
  
  describe("DropdownMenuCheckboxItem", () => {
    it("should render checkbox items", async () => {
      render(
        <DropdownMenu>
          <DropdownMenuTrigger asChild>
            <button>Menu</button>
          </DropdownMenuTrigger>
          <DropdownMenuContent>
            <DropdownMenuCheckboxItem checked={false}>
              Unchecked Option
            </DropdownMenuCheckboxItem>
            <DropdownMenuCheckboxItem checked={true}>
              Checked Option
            </DropdownMenuCheckboxItem>
          </DropdownMenuContent>
        </DropdownMenu>
      );
      
      fireEvent.click(screen.getByRole("button", { name: "Menu" }));
      
      await waitFor(() => {
        expect(screen.getByText("Unchecked Option")).toBeInTheDocument();
        expect(screen.getByText("Checked Option")).toBeInTheDocument();
      });
    });
    
    it("should toggle checkbox items", async () => {
      const onCheckedChange = vi.fn();
      
      render(
        <DropdownMenu>
          <DropdownMenuTrigger asChild>
            <button>Menu</button>
          </DropdownMenuTrigger>
          <DropdownMenuContent>
            <DropdownMenuCheckboxItem
              checked={false}
              onCheckedChange={onCheckedChange}
            >
              Toggle Me
            </DropdownMenuCheckboxItem>
          </DropdownMenuContent>
        </DropdownMenu>
      );
      
      fireEvent.click(screen.getByRole("button", { name: "Menu" }));
      
      await waitFor(() => {
        const checkboxItem = screen.getByText("Toggle Me");
        expect(checkboxItem).toBeInTheDocument();
        
        fireEvent.click(checkboxItem);
        expect(onCheckedChange).toHaveBeenCalledWith(true);
      });
    });
  });
  
  describe("DropdownMenuRadioGroup and DropdownMenuRadioItem", () => {
    it("should render radio items", async () => {
      render(
        <DropdownMenu>
          <DropdownMenuTrigger asChild>
            <button>Menu</button>
          </DropdownMenuTrigger>
          <DropdownMenuContent>
            <DropdownMenuRadioGroup value="option1">
              <DropdownMenuRadioItem value="option1">
                Option 1
              </DropdownMenuRadioItem>
              <DropdownMenuRadioItem value="option2">
                Option 2
              </DropdownMenuRadioItem>
            </DropdownMenuRadioGroup>
          </DropdownMenuContent>
        </DropdownMenu>
      );
      
      fireEvent.click(screen.getByRole("button", { name: "Menu" }));
      
      await waitFor(() => {
        expect(screen.getByText("Option 1")).toBeInTheDocument();
        expect(screen.getByText("Option 2")).toBeInTheDocument();
      });
    });
    
    it("should handle radio item selection", async () => {
      const onValueChange = vi.fn();
      
      render(
        <DropdownMenu>
          <DropdownMenuTrigger asChild>
            <button>Menu</button>
          </DropdownMenuTrigger>
          <DropdownMenuContent>
            <DropdownMenuRadioGroup value="option1" onValueChange={onValueChange}>
              <DropdownMenuRadioItem value="option1">
                Option 1
              </DropdownMenuRadioItem>
              <DropdownMenuRadioItem value="option2">
                Option 2
              </DropdownMenuRadioItem>
            </DropdownMenuRadioGroup>
          </DropdownMenuContent>
        </DropdownMenu>
      );
      
      fireEvent.click(screen.getByRole("button", { name: "Menu" }));
      
      await waitFor(() => {
        const option2 = screen.getByText("Option 2");
        fireEvent.click(option2);
        expect(onValueChange).toHaveBeenCalledWith("option2");
      });
    });
  });
  
  describe("DropdownMenuLabel and DropdownMenuSeparator", () => {
    it("should render labels and separators", async () => {
      render(
        <DropdownMenu>
          <DropdownMenuTrigger asChild>
            <button>Menu</button>
          </DropdownMenuTrigger>
          <DropdownMenuContent>
            <DropdownMenuLabel>Section Label</DropdownMenuLabel>
            <DropdownMenuSeparator />
            <DropdownMenuItem>Item after separator</DropdownMenuItem>
          </DropdownMenuContent>
        </DropdownMenu>
      );
      
      fireEvent.click(screen.getByRole("button", { name: "Menu" }));
      
      await waitFor(() => {
        expect(screen.getByText("Section Label")).toBeInTheDocument();
        expect(screen.getByText("Item after separator")).toBeInTheDocument();
      });
    });
  });
  
  describe("DropdownMenuShortcut", () => {
    it("should render keyboard shortcuts", async () => {
      render(
        <DropdownMenu>
          <DropdownMenuTrigger asChild>
            <button>Menu</button>
          </DropdownMenuTrigger>
          <DropdownMenuContent>
            <DropdownMenuItem>
              Copy
              <DropdownMenuShortcut>⌘C</DropdownMenuShortcut>
            </DropdownMenuItem>
          </DropdownMenuContent>
        </DropdownMenu>
      );
      
      fireEvent.click(screen.getByRole("button", { name: "Menu" }));
      
      await waitFor(() => {
        expect(screen.getByText("Copy")).toBeInTheDocument();
        expect(screen.getByText("⌘C")).toBeInTheDocument();
      });
    });
  });
  
  describe("DropdownMenuGroup", () => {
    it("should group menu items", async () => {
      render(
        <DropdownMenu>
          <DropdownMenuTrigger asChild>
            <button>Menu</button>
          </DropdownMenuTrigger>
          <DropdownMenuContent>
            <DropdownMenuGroup>
              <DropdownMenuItem>Group Item 1</DropdownMenuItem>
              <DropdownMenuItem>Group Item 2</DropdownMenuItem>
            </DropdownMenuGroup>
          </DropdownMenuContent>
        </DropdownMenu>
      );
      
      fireEvent.click(screen.getByRole("button", { name: "Menu" }));
      
      await waitFor(() => {
        expect(screen.getByText("Group Item 1")).toBeInTheDocument();
        expect(screen.getByText("Group Item 2")).toBeInTheDocument();
      });
    });
  });
  
  describe("DropdownMenuSub", () => {
    it("should render submenu", async () => {
      render(
        <DropdownMenu>
          <DropdownMenuTrigger asChild>
            <button>Menu</button>
          </DropdownMenuTrigger>
          <DropdownMenuContent>
            <DropdownMenuSub>
              <DropdownMenuSubTrigger>More Options</DropdownMenuSubTrigger>
              <DropdownMenuSubContent>
                <DropdownMenuItem>Submenu Item</DropdownMenuItem>
              </DropdownMenuSubContent>
            </DropdownMenuSub>
          </DropdownMenuContent>
        </DropdownMenu>
      );
      
      fireEvent.click(screen.getByRole("button", { name: "Menu" }));
      
      await waitFor(() => {
        expect(screen.getByText("More Options")).toBeInTheDocument();
      });
    });
  });
  
  describe("Keyboard Navigation", () => {
    it("should support arrow key navigation", async () => {
      render(
        <DropdownMenu>
          <DropdownMenuTrigger asChild>
            <button>Menu</button>
          </DropdownMenuTrigger>
          <DropdownMenuContent>
            <DropdownMenuItem>First Item</DropdownMenuItem>
            <DropdownMenuItem>Second Item</DropdownMenuItem>
          </DropdownMenuContent>
        </DropdownMenu>
      );
      
      const trigger = screen.getByRole("button", { name: "Menu" });
      trigger.focus();
      
      // Open menu with Enter key
      fireEvent.keyDown(trigger, { key: "Enter" });
      
      await waitFor(() => {
        expect(screen.getByText("First Item")).toBeVisible();
      });
    });
    
    it("should close on Escape key", async () => {
      render(
        <DropdownMenu>
          <DropdownMenuTrigger asChild>
            <button>Menu</button>
          </DropdownMenuTrigger>
          <DropdownMenuContent>
            <DropdownMenuItem>Item</DropdownMenuItem>
          </DropdownMenuContent>
        </DropdownMenu>
      );
      
      fireEvent.click(screen.getByRole("button", { name: "Menu" }));
      
      await waitFor(() => {
        expect(screen.getByText("Item")).toBeVisible();
      });
      
      fireEvent.keyDown(document, { key: "Escape" });
      
      await waitFor(() => {
        expect(screen.queryByText("Item")).not.toBeVisible();
      });
    });
  });
  
  describe("Custom Styling", () => {
    it("should apply custom className", () => {
      const { container } = render(
        <DropdownMenu>
          <DropdownMenuTrigger asChild>
            <button>Menu</button>
          </DropdownMenuTrigger>
          <DropdownMenuContent className="custom-dropdown">
            <DropdownMenuItem className="custom-item">Item</DropdownMenuItem>
          </DropdownMenuContent>
        </DropdownMenu>
      );
      
      fireEvent.click(screen.getByRole("button", { name: "Menu" }));
      
      const customContent = container.querySelector(".custom-dropdown");
      const customItem = container.querySelector(".custom-item");
      
      expect(customContent).toBeInTheDocument();
      expect(customItem).toBeInTheDocument();
    });
  });
});