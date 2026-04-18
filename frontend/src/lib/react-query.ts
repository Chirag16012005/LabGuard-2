"use client";

import { QueryClient } from "@tanstack/react-query";

let queryClient: QueryClient | null = null;

export function getQueryClient(): QueryClient {
  if (!queryClient) {
    queryClient = new QueryClient({
      defaultOptions: {
        queries: {
          staleTime: 60 * 1000,
          retry: false, // Don't retry failed queries automatically (backend may be down)
          refetchOnWindowFocus: false, // Don't refetch when tab regains focus
          refetchOnReconnect: false, // Don't auto-refetch on network reconnect
        },
      },
    });
  }
  return queryClient;
}
