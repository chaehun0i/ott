import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { BrowserRouter } from "react-router-dom";
import "@/styles/tokens.css";

const queryClient = new QueryClient();

export function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        <main>
          <h1>OTT Feed</h1>
        </main>
      </BrowserRouter>
    </QueryClientProvider>
  );
}
