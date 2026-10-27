import { StrictMode } from "react";
import { createRoot } from "react-dom/client";
import { ClaimsApp } from "./ClaimsApp";
import "./portal.css";

createRoot(document.getElementById("root")!).render(
  <StrictMode>
    <ClaimsApp />
  </StrictMode>,
);
