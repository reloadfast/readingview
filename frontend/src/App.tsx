import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { createBrowserRouter, RouterProvider } from "react-router-dom";
import { AppLayout } from "@/components/layout";
import DashboardPage   from "@/pages/DashboardPage";
import LibraryPage     from "@/pages/LibraryPage";
import StatisticsPage  from "@/pages/StatisticsPage";
import AuthorsPage     from "@/pages/AuthorsPage";
import NarratorsPage   from "@/pages/NarratorsPage";
import SeriesPage      from "@/pages/SeriesPage";
import ReleasesPage    from "@/pages/ReleasesPage";
import CollectionsPage from "@/pages/CollectionsPage";
import SettingsPage    from "@/pages/SettingsPage";

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
      { path: "/narrators",   element: <NarratorsPage />   },
      { path: "/series",      element: <SeriesPage />      },
      { path: "/releases",    element: <ReleasesPage />    },
      { path: "/collections", element: <CollectionsPage /> },
      { path: "/settings",    element: <SettingsPage />    },
    ],
  },
]);

export default function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <RouterProvider router={router} />
    </QueryClientProvider>
  );
}
