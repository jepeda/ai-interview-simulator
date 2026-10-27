import { StrictMode } from "react";
import { createRoot } from "react-dom/client";
import { WeekApp } from "./WeekApp";
import "./app.css";

createRoot(document.getElementById("root")!).render(
  <StrictMode>
    <WeekApp />
  </StrictMode>,
);
