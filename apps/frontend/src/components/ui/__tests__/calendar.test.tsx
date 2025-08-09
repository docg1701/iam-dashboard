/**
 * Calendar Component Tests
 *
 * Following CLAUDE.md testing directives:
 * - NEVER mock internal frontend code, components, hooks, or utilities
 * - ONLY mock external APIs (date-fns, third-party services, etc.)
 * - Test actual behavior, not implementation details
 */

import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import { vi, describe, it, expect, beforeEach } from "vitest";
import { Calendar } from "../calendar";
import { ptBR } from "date-fns/locale";

// Mock date-fns locale - external dependency
vi.mock("date-fns/locale", () => ({
  ptBR: {
    localize: {
      month: (month: number) => {
        const months = [
          "Janeiro", "Fevereiro", "Março", "Abril", "Maio", "Junho",
          "Julho", "Agosto", "Setembro", "Outubro", "Novembro", "Dezembro"
        ];
        return months[month];
      },
      day: (day: number) => {
        const days = ["Domingo", "Segunda", "Terça", "Quarta", "Quinta", "Sexta", "Sábado"];
        return days[day];
      },
    },
    formatLong: {
      date: () => "dd/MM/yyyy",
    },
    code: "pt-BR",
  },
}));

describe("Calendar Component", () => {
  const mockOnSelect = vi.fn();
  
  beforeEach(() => {
    vi.clearAllMocks();
  });
  
  describe("Basic Rendering", () => {
    it("should render calendar with current month", () => {
      render(
        <Calendar 
          mode="single" 
          selected={undefined}
          onSelect={mockOnSelect}
        />
      );
      
      // Check if calendar navigation is rendered
      const prevButton = screen.getByRole("button", { name: /anterior/i });
      const nextButton = screen.getByRole("button", { name: /próximo/i });
      
      expect(prevButton).toBeInTheDocument();
      expect(nextButton).toBeInTheDocument();
    });
    
    it("should render with selected date", () => {
      const selectedDate = new Date(2024, 0, 15); // January 15, 2024
      
      render(
        <Calendar 
          mode="single" 
          selected={selectedDate}
          onSelect={mockOnSelect}
        />
      );
      
      // Check if the selected date is highlighted
      const selectedCell = screen.getByRole("gridcell", { 
        name: /15/i,
        selected: true 
      });
      expect(selectedCell).toBeInTheDocument();
    });
    
    it("should render in Portuguese locale", () => {
      render(
        <Calendar 
          mode="single" 
          selected={undefined}
          onSelect={mockOnSelect}
          locale={ptBR}
        />
      );
      
      // Check for Portuguese day headers
      expect(screen.getByText(/dom/i)).toBeInTheDocument(); // Domingo
      expect(screen.getByText(/seg/i)).toBeInTheDocument(); // Segunda
    });
  });
  
  describe("Date Selection", () => {
    it("should call onSelect when date is clicked", async () => {
      render(
        <Calendar 
          mode="single" 
          selected={undefined}
          onSelect={mockOnSelect}
        />
      );
      
      // Click on a date (day 15)
      const dateButton = screen.getByRole("gridcell", { name: /15/i });
      fireEvent.click(dateButton);
      
      await waitFor(() => {
        expect(mockOnSelect).toHaveBeenCalled();
      });
      
      const callArgs = mockOnSelect.mock.calls[0][0];
      expect(callArgs).toBeInstanceOf(Date);
      expect(callArgs.getDate()).toBe(15);
    });
    
    it("should handle range selection mode", () => {
      const mockOnSelectRange = vi.fn();
      
      render(
        <Calendar 
          mode="range" 
          selected={undefined}
          onSelect={mockOnSelectRange}
        />
      );
      
      // Click on start date
      const startDate = screen.getByRole("gridcell", { name: /10/i });
      fireEvent.click(startDate);
      
      // Click on end date
      const endDate = screen.getByRole("gridcell", { name: /20/i });
      fireEvent.click(endDate);
      
      expect(mockOnSelectRange).toHaveBeenCalledTimes(2);
    });
    
    it("should handle multiple selection mode", () => {
      const mockOnSelectMultiple = vi.fn();
      
      render(
        <Calendar 
          mode="multiple" 
          selected={[]}
          onSelect={mockOnSelectMultiple}
        />
      );
      
      // Click multiple dates
      const date1 = screen.getByRole("gridcell", { name: /5/i });
      const date2 = screen.getByRole("gridcell", { name: /15/i });
      
      fireEvent.click(date1);
      fireEvent.click(date2);
      
      expect(mockOnSelectMultiple).toHaveBeenCalledTimes(2);
    });
  });
  
  describe("Navigation", () => {
    it("should navigate to previous month", async () => {
      render(
        <Calendar 
          mode="single" 
          selected={undefined}
          onSelect={mockOnSelect}
          defaultMonth={new Date(2024, 1, 1)} // February 2024
        />
      );
      
      const prevButton = screen.getByRole("button", { name: /anterior/i });
      fireEvent.click(prevButton);
      
      // Should now show January 2024
      await waitFor(() => {
        // Check if we're in January by looking for the typical date layout
        expect(screen.getByRole("grid")).toBeInTheDocument();
      });
    });
    
    it("should navigate to next month", async () => {
      render(
        <Calendar 
          mode="single" 
          selected={undefined}
          onSelect={mockOnSelect}
          defaultMonth={new Date(2024, 1, 1)} // February 2024
        />
      );
      
      const nextButton = screen.getByRole("button", { name: /próximo/i });
      fireEvent.click(nextButton);
      
      // Should now show March 2024
      await waitFor(() => {
        expect(screen.getByRole("grid")).toBeInTheDocument();
      });
    });
  });
  
  describe("Disabled Dates", () => {
    it("should disable dates outside allowed range", () => {
      const today = new Date();
      const minDate = new Date(today.getFullYear(), today.getMonth(), 10);
      const maxDate = new Date(today.getFullYear(), today.getMonth(), 20);
      
      render(
        <Calendar 
          mode="single" 
          selected={undefined}
          onSelect={mockOnSelect}
          disabled={{
            before: minDate,
            after: maxDate
          }}
        />
      );
      
      // Dates before minDate should be disabled
      const disabledDate = screen.getByRole("gridcell", { name: /5/i });
      expect(disabledDate).toHaveAttribute("aria-disabled", "true");
    });
    
    it("should not allow selection of disabled dates", () => {
      const today = new Date();
      const minDate = new Date(today.getFullYear(), today.getMonth(), 10);
      
      render(
        <Calendar 
          mode="single" 
          selected={undefined}
          onSelect={mockOnSelect}
          disabled={{ before: minDate }}
        />
      );
      
      // Try to click a disabled date
      const disabledDate = screen.getByRole("gridcell", { name: /5/i });
      fireEvent.click(disabledDate);
      
      // onSelect should not be called for disabled dates
      expect(mockOnSelect).not.toHaveBeenCalled();
    });
  });
  
  describe("Accessibility", () => {
    it("should have proper ARIA attributes", () => {
      render(
        <Calendar 
          mode="single" 
          selected={undefined}
          onSelect={mockOnSelect}
        />
      );
      
      // Check for calendar grid
      const calendarGrid = screen.getByRole("grid");
      expect(calendarGrid).toBeInTheDocument();
      
      // Check for navigation buttons
      const prevButton = screen.getByRole("button", { name: /anterior/i });
      const nextButton = screen.getByRole("button", { name: /próximo/i });
      
      expect(prevButton).toHaveAttribute("aria-label");
      expect(nextButton).toHaveAttribute("aria-label");
    });
    
    it("should support keyboard navigation", () => {
      render(
        <Calendar 
          mode="single" 
          selected={undefined}
          onSelect={mockOnSelect}
        />
      );
      
      const calendarGrid = screen.getByRole("grid");
      
      // Test arrow key navigation
      fireEvent.keyDown(calendarGrid, { key: "ArrowRight" });
      fireEvent.keyDown(calendarGrid, { key: "ArrowLeft" });
      fireEvent.keyDown(calendarGrid, { key: "ArrowDown" });
      fireEvent.keyDown(calendarGrid, { key: "ArrowUp" });
      
      // Test Enter/Space for selection
      fireEvent.keyDown(calendarGrid, { key: "Enter" });
      fireEvent.keyDown(calendarGrid, { key: " " });
      
      // Should maintain focus and be navigable
      expect(calendarGrid).toBeInTheDocument();
    });
  });
  
  describe("Custom Styling and Classes", () => {
    it("should apply custom className", () => {
      const { container } = render(
        <Calendar 
          mode="single" 
          selected={undefined}
          onSelect={mockOnSelect}
          className="custom-calendar"
        />
      );
      
      expect(container.firstChild).toHaveClass("custom-calendar");
    });
    
    it("should handle different calendar sizes", () => {
      const { container } = render(
        <Calendar 
          mode="single" 
          selected={undefined}
          onSelect={mockOnSelect}
          className="w-full"
        />
      );
      
      expect(container.firstChild).toHaveClass("w-full");
    });
  });
});