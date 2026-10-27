import { StrictMode } from "react";
import { createRoot } from "react-dom/client";
import { BalancesApp } from "./BalancesApp";
import "./app.css";

createRoot(document.getElementById("root")!).render(
  <StrictMode>
    <BalancesApp />
  </StrictMode>,
);
