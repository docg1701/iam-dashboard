/**
 * Tabs Component Tests
 *
 * Following CLAUDE.md testing directives:
 * - NEVER mock internal frontend code, components, hooks, or utilities
 * - ONLY mock external APIs (third-party services, etc.)
 * - Test actual behavior, not implementation details
 */

import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import { vi, describe, it, expect, beforeEach } from "vitest";
import { Tabs, TabsList, TabsTrigger, TabsContent } from "../tabs";

describe("Tabs Components", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });
  
  describe("Basic Rendering", () => {
    it("should render tabs with content", () => {
      render(
        <Tabs defaultValue="tab1">
          <TabsList>
            <TabsTrigger value="tab1">Aba 1</TabsTrigger>
            <TabsTrigger value="tab2">Aba 2</TabsTrigger>
          </TabsList>
          <TabsContent value="tab1">Conteúdo da Aba 1</TabsContent>
          <TabsContent value="tab2">Conteúdo da Aba 2</TabsContent>
        </Tabs>
      );
      
      // Check if tab buttons are rendered
      expect(screen.getByRole("tab", { name: "Aba 1" })).toBeInTheDocument();
      expect(screen.getByRole("tab", { name: "Aba 2" })).toBeInTheDocument();
      
      // Check if default content is visible
      expect(screen.getByText("Conteúdo da Aba 1")).toBeVisible();
      expect(screen.queryByText("Conteúdo da Aba 2")).not.toBeVisible();
    });
    
    it("should render tabs list with proper role", () => {
      render(
        <Tabs defaultValue="tab1">
          <TabsList>
            <TabsTrigger value="tab1">Aba 1</TabsTrigger>
          </TabsList>
          <TabsContent value="tab1">Conteúdo</TabsContent>
        </Tabs>
      );
      
      const tabList = screen.getByRole("tablist");
      expect(tabList).toBeInTheDocument();
    });
    
    it("should render tab content with proper role", () => {
      render(
        <Tabs defaultValue="tab1">
          <TabsList>
            <TabsTrigger value="tab1">Aba 1</TabsTrigger>
          </TabsList>
          <TabsContent value="tab1">Conteúdo da aba</TabsContent>
        </Tabs>
      );
      
      const tabPanel = screen.getByRole("tabpanel");
      expect(tabPanel).toBeInTheDocument();
      expect(tabPanel).toHaveTextContent("Conteúdo da aba");
    });
  });
  
  describe("Tab Navigation", () => {
    it("should switch tabs when clicked", async () => {
      render(
        <Tabs defaultValue="tab1">
          <TabsList>
            <TabsTrigger value="tab1">Aba 1</TabsTrigger>
            <TabsTrigger value="tab2">Aba 2</TabsTrigger>
          </TabsList>
          <TabsContent value="tab1">Conteúdo da Aba 1</TabsContent>
          <TabsContent value="tab2">Conteúdo da Aba 2</TabsContent>
        </Tabs>
      );
      
      const tab2 = screen.getByRole("tab", { name: "Aba 2" });
      fireEvent.click(tab2);
      
      await waitFor(() => {
        expect(screen.getByText("Conteúdo da Aba 2")).toBeVisible();
        expect(screen.queryByText("Conteúdo da Aba 1")).not.toBeVisible();
      });
    });
    
    it("should maintain active state on selected tab", async () => {
      render(
        <Tabs defaultValue="tab1">
          <TabsList>
            <TabsTrigger value="tab1">Aba 1</TabsTrigger>
            <TabsTrigger value="tab2">Aba 2</TabsTrigger>
          </TabsList>
          <TabsContent value="tab1">Conteúdo 1</TabsContent>
          <TabsContent value="tab2">Conteúdo 2</TabsContent>
        </Tabs>
      );
      
      const tab1 = screen.getByRole("tab", { name: "Aba 1" });
      const tab2 = screen.getByRole("tab", { name: "Aba 2" });
      
      // Initially tab1 should be selected
      expect(tab1).toHaveAttribute("aria-selected", "true");
      expect(tab2).toHaveAttribute("aria-selected", "false");
      
      // Click tab2
      fireEvent.click(tab2);
      
      await waitFor(() => {
        expect(tab2).toHaveAttribute("aria-selected", "true");
        expect(tab1).toHaveAttribute("aria-selected", "false");
      });
    });
  });
  
  describe("Keyboard Navigation", () => {
    it("should navigate tabs with arrow keys", async () => {
      render(
        <Tabs defaultValue="tab1">
          <TabsList>
            <TabsTrigger value="tab1">Aba 1</TabsTrigger>
            <TabsTrigger value="tab2">Aba 2</TabsTrigger>
            <TabsTrigger value="tab3">Aba 3</TabsTrigger>
          </TabsList>
          <TabsContent value="tab1">Conteúdo 1</TabsContent>
          <TabsContent value="tab2">Conteúdo 2</TabsContent>
          <TabsContent value="tab3">Conteúdo 3</TabsContent>
        </Tabs>
      );
      
      const tab1 = screen.getByRole("tab", { name: "Aba 1" });
      const tab2 = screen.getByRole("tab", { name: "Aba 2" });
      
      // Focus on first tab
      tab1.focus();
      
      // Navigate right
      fireEvent.keyDown(tab1, { key: "ArrowRight" });
      
      await waitFor(() => {
        expect(tab2).toHaveFocus();
      });
    });
    
    it("should activate tab on Enter key", async () => {
      render(
        <Tabs defaultValue="tab1">
          <TabsList>
            <TabsTrigger value="tab1">Aba 1</TabsTrigger>
            <TabsTrigger value="tab2">Aba 2</TabsTrigger>
          </TabsList>
          <TabsContent value="tab1">Conteúdo 1</TabsContent>
          <TabsContent value="tab2">Conteúdo 2</TabsContent>
        </Tabs>
      );
      
      const tab2 = screen.getByRole("tab", { name: "Aba 2" });
      tab2.focus();
      
      fireEvent.keyDown(tab2, { key: "Enter" });
      
      await waitFor(() => {
        expect(screen.getByText("Conteúdo 2")).toBeVisible();
      });
    });
    
    it("should activate tab on Space key", async () => {
      render(
        <Tabs defaultValue="tab1">
          <TabsList>
            <TabsTrigger value="tab1">Aba 1</TabsTrigger>
            <TabsTrigger value="tab2">Aba 2</TabsTrigger>
          </TabsList>
          <TabsContent value="tab1">Conteúdo 1</TabsContent>
          <TabsContent value="tab2">Conteúdo 2</TabsContent>
        </Tabs>
      );
      
      const tab2 = screen.getByRole("tab", { name: "Aba 2" });
      tab2.focus();
      
      fireEvent.keyDown(tab2, { key: " " });
      
      await waitFor(() => {
        expect(screen.getByText("Conteúdo 2")).toBeVisible();
      });
    });
  });
  
  describe("Controlled Mode", () => {
    it("should work in controlled mode with value prop", async () => {
      const onValueChange = vi.fn();
      
      const { rerender } = render(
        <Tabs value="tab1" onValueChange={onValueChange}>
          <TabsList>
            <TabsTrigger value="tab1">Aba 1</TabsTrigger>
            <TabsTrigger value="tab2">Aba 2</TabsTrigger>
          </TabsList>
          <TabsContent value="tab1">Conteúdo 1</TabsContent>
          <TabsContent value="tab2">Conteúdo 2</TabsContent>
        </Tabs>
      );
      
      // Content 1 should be visible
      expect(screen.getByText("Conteúdo 1")).toBeVisible();
      
      // Click tab 2
      const tab2 = screen.getByRole("tab", { name: "Aba 2" });
      fireEvent.click(tab2);
      
      // onValueChange should be called
      expect(onValueChange).toHaveBeenCalledWith("tab2");
      
      // Rerender with new value
      rerender(
        <Tabs value="tab2" onValueChange={onValueChange}>
          <TabsList>
            <TabsTrigger value="tab1">Aba 1</TabsTrigger>
            <TabsTrigger value="tab2">Aba 2</TabsTrigger>
          </TabsList>
          <TabsContent value="tab1">Conteúdo 1</TabsContent>
          <TabsContent value="tab2">Conteúdo 2</TabsContent>
        </Tabs>
      );
      
      // Now content 2 should be visible
      expect(screen.getByText("Conteúdo 2")).toBeVisible();
      expect(screen.queryByText("Conteúdo 1")).not.toBeVisible();
    });
  });
  
  describe("Multiple Tab Sets", () => {
    it("should handle multiple independent tab sets", () => {
      render(
        <div>
          <Tabs defaultValue="set1-tab1">
            <TabsList>
              <TabsTrigger value="set1-tab1">Set1 Aba 1</TabsTrigger>
              <TabsTrigger value="set1-tab2">Set1 Aba 2</TabsTrigger>
            </TabsList>
            <TabsContent value="set1-tab1">Set1 Conteúdo 1</TabsContent>
            <TabsContent value="set1-tab2">Set1 Conteúdo 2</TabsContent>
          </Tabs>
          
          <Tabs defaultValue="set2-tab1">
            <TabsList>
              <TabsTrigger value="set2-tab1">Set2 Aba 1</TabsTrigger>
              <TabsTrigger value="set2-tab2">Set2 Aba 2</TabsTrigger>
            </TabsList>
            <TabsContent value="set2-tab1">Set2 Conteúdo 1</TabsContent>
            <TabsContent value="set2-tab2">Set2 Conteúdo 2</TabsContent>
          </Tabs>
        </div>
      );
      
      // Both sets should show their default content
      expect(screen.getByText("Set1 Conteúdo 1")).toBeVisible();
      expect(screen.getByText("Set2 Conteúdo 1")).toBeVisible();
      
      // Interact with first set
      fireEvent.click(screen.getByRole("tab", { name: "Set1 Aba 2" }));
      
      // Only first set should change
      expect(screen.getByText("Set1 Conteúdo 2")).toBeVisible();
      expect(screen.getByText("Set2 Conteúdo 1")).toBeVisible();
    });
  });
  
  describe("Styling and Custom Classes", () => {
    it("should apply custom className to Tabs root", () => {
      const { container } = render(
        <Tabs defaultValue="tab1" className="custom-tabs">
          <TabsList>
            <TabsTrigger value="tab1">Aba</TabsTrigger>
          </TabsList>
          <TabsContent value="tab1">Conteúdo</TabsContent>
        </Tabs>
      );
      
      expect(container.firstChild).toHaveClass("custom-tabs");
    });
    
    it("should apply custom className to TabsList", () => {
      render(
        <Tabs defaultValue="tab1">
          <TabsList className="custom-tabs-list">
            <TabsTrigger value="tab1">Aba</TabsTrigger>
          </TabsList>
          <TabsContent value="tab1">Conteúdo</TabsContent>
        </Tabs>
      );
      
      const tabsList = screen.getByRole("tablist");
      expect(tabsList).toHaveClass("custom-tabs-list");
    });
    
    it("should apply custom className to TabsTrigger", () => {
      render(
        <Tabs defaultValue="tab1">
          <TabsList>
            <TabsTrigger value="tab1" className="custom-tab-trigger">Aba</TabsTrigger>
          </TabsList>
          <TabsContent value="tab1">Conteúdo</TabsContent>
        </Tabs>
      );
      
      const tab = screen.getByRole("tab", { name: "Aba" });
      expect(tab).toHaveClass("custom-tab-trigger");
    });
    
    it("should apply custom className to TabsContent", () => {
      render(
        <Tabs defaultValue="tab1">
          <TabsList>
            <TabsTrigger value="tab1">Aba</TabsTrigger>
          </TabsList>
          <TabsContent value="tab1" className="custom-tab-content">
            Conteúdo personalizado
          </TabsContent>
        </Tabs>
      );
      
      const tabPanel = screen.getByRole("tabpanel");
      expect(tabPanel).toHaveClass("custom-tab-content");
    });
  });
  
  describe("Accessibility", () => {
    it("should have proper ARIA relationships", () => {
      render(
        <Tabs defaultValue="tab1">
          <TabsList>
            <TabsTrigger value="tab1">Aba 1</TabsTrigger>
            <TabsTrigger value="tab2">Aba 2</TabsTrigger>
          </TabsList>
          <TabsContent value="tab1">Conteúdo 1</TabsContent>
          <TabsContent value="tab2">Conteúdo 2</TabsContent>
        </Tabs>
      );
      
      const tab1 = screen.getByRole("tab", { name: "Aba 1" });
      const tabPanel = screen.getByRole("tabpanel");
      
      // Tab should control the panel
      expect(tab1).toHaveAttribute("aria-controls");
      expect(tabPanel).toHaveAttribute("aria-labelledby");
      
      // The IDs should match
      const controlsId = tab1.getAttribute("aria-controls");
      const labeledById = tabPanel.getAttribute("aria-labelledby");
      
      expect(tabPanel).toHaveAttribute("id", controlsId);
      expect(tab1).toHaveAttribute("id", labeledById);
    });
    
    it("should support disabled tabs", () => {
      render(
        <Tabs defaultValue="tab1">
          <TabsList>
            <TabsTrigger value="tab1">Aba Ativa</TabsTrigger>
            <TabsTrigger value="tab2" disabled>Aba Desabilitada</TabsTrigger>
          </TabsList>
          <TabsContent value="tab1">Conteúdo ativo</TabsContent>
          <TabsContent value="tab2">Conteúdo desabilitado</TabsContent>
        </Tabs>
      );
      
      const disabledTab = screen.getByRole("tab", { name: "Aba Desabilitada" });
      
      expect(disabledTab).toHaveAttribute("aria-disabled", "true");
      expect(disabledTab).toBeDisabled();
      
      // Clicking disabled tab should not change content
      fireEvent.click(disabledTab);
      expect(screen.getByText("Conteúdo ativo")).toBeVisible();
      expect(screen.queryByText("Conteúdo desabilitado")).not.toBeVisible();
    });
  });
});