import { ReactElement } from "react";
import { render } from "@testing-library/react";

export function renderWithProviders(ui: ReactElement) {
  return render(ui);
}
