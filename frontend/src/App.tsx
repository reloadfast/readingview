import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { createBrowserRouter, RouterProvider } from "react-router-dom";
import { AppLayout } from "@/components/layout";
import { WebSocketProvider } from "@/contexts/WebSocketContext";
import DashboardPage   from "@/pages/DashboardPage";
import LibraryPage     from "@/pages/LibraryPage";
import StatisticsPage  from "@/pages/StatisticsPage";
import AuthorsPage     from "@/pages/AuthorsPage";
import NarratorsPage   from "@/pages/NarratorsPage";
import SeriesPage      from "@/pages/SeriesPage";
import ReleasesPage    from "@/pages/ReleasesPage";
import CollectionsPage      from "@/pages/CollectionsPage";
import RecommendationsPage  from "@/pages/RecommendationsPage";
import SettingsPage         from "@/pages/SettingsPage";
import AuthorBooksPage      from "@/pages/AuthorBooksPage";
import NarratorBooksPage    from "@/pages/NarratorBooksPage";

const queryClient = new QueryClient({
  defaultOptions: {
    queries: { staleTime: 30_000, retry: 1 },
  },
});

const router = createBrowserRouter([
  {
    element: <AppLayout />,
    children: [
      { path: "/",            element: <DashboardPage />   },
      { path: "/library",     element: <LibraryPage />     },
      { path: "/statistics",  element: <StatisticsPage />  },
      { path: "/authors",     element: <AuthorsPage />     },
      { path: "/authors/:name", element: <AuthorBooksPage /> },
      { path: "/narrators",   element: <NarratorsPage />   },
      { path: "/narrators/:name", element: <NarratorBooksPage /> },
      { path: "/series",      element: <SeriesPage />      },
      { path: "/releases",    element: <ReleasesPage />    },
      { path: "/collections",    element: <CollectionsPage />     },
      { path: "/recommendations", element: <RecommendationsPage /> },
      { path: "/settings",       element: <SettingsPage />        },
    ],
  },
]);

export default function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <WebSocketProvider queryClient={queryClient}>
        <RouterProvider router={router} />
      </WebSocketProvider>
    </QueryClientProvider>
  );
}
