import React from "react";
import { createRoot } from "react-dom/client";

const root = document.getElementById("root");

if (!root) {
  throw new Error("Missing application root");
}

createRoot(root).render(
  <React.StrictMode>
    <main>
      <h1>OTT Feed</h1>
    </main>
  </React.StrictMode>,
);
