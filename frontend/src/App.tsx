import { useEffect, useMemo, useRef, useState } from "react";
import { Loader2, Music2, RefreshCcw, Shuffle } from "lucide-react";
import { Toaster, toast } from "sonner";

import {
  fetchCatalogStatus,
  fetchRandomAlbum,
  refreshCatalog,
  type AgeBucket,
  type Album,
  type CatalogStatus,
} from "@/api";
import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardFooter,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from "@/components/ui/tooltip";
import { ToggleGroup, ToggleGroupItem } from "@/components/ui/toggle-group";
import { cn } from "@/lib/utils";
import {
  Accordion,
  AccordionContent,
  AccordionItem,
  AccordionTrigger,
} from "@/components/ui/accordion";

const AGE_OPTIONS: { value: AgeBucket; label: string }[] = [
  { value: "old", label: "Old" },
  { value: "medium", label: "Medium" },
  { value: "new", label: "New" },
  { value: "all", label: "All" },
];

export default function App() {
  const [album, setAlbum] = useState<Album | null>(null);
  const [runtime, setRuntime] = useState<string | null>(null);
  const [selectedAge, setSelectedAge] = useState<AgeBucket>("all");
  const [loading, setLoading] = useState(true);
  const [status, setStatus] = useState<CatalogStatus | null>(null);
  const [refreshing, setRefreshing] = useState(false);
  const [albumKey, setAlbumKey] = useState(0);
  const controllerRef = useRef<AbortController | null>(null);
  const requestIdRef = useRef(0);

  useEffect(() => {
    let active = true;
    let timeoutId: number | undefined;

    const poll = async () => {
      try {
        const data = await fetchCatalogStatus();
        if (!active) {
          return;
        }
        setStatus(data);
        const delay = data.state === "running" ? 3000 : 15000;
        timeoutId = window.setTimeout(poll, delay);
      } catch {
        timeoutId = window.setTimeout(poll, 15000);
      }
    };

    poll();

    return () => {
      active = false;
      if (timeoutId) {
        window.clearTimeout(timeoutId);
      }
    };
  }, []);

  useEffect(() => {
    void loadAlbum(undefined, false);
    return () => {
      if (controllerRef.current) {
        controllerRef.current.abort();
      }
    };
  }, []);

  const loadAlbum = async (age: AgeBucket | undefined, reroll: boolean) => {
    if (controllerRef.current) {
      controllerRef.current.abort();
    }
    const controller = new AbortController();
    controllerRef.current = controller;
    const requestId = ++requestIdRef.current;
    setLoading(true);

    try {
      const data = await fetchRandomAlbum(age, reroll, controller.signal);
      setAlbum(data.album);
      setRuntime(data.runtime_str);
      setSelectedAge(data.age);
      setAlbumKey((prev) => prev + 1);
    } catch (error) {
      if (error instanceof DOMException && error.name === "AbortError") {
        return;
      }
      const message =
        error instanceof Error && error.message === "no_albums"
          ? "No albums available for this bucket."
          : "Could not load a new album.";
      toast.error(message);
    } finally {
      if (requestId === requestIdRef.current) {
        setLoading(false);
      }
    }
  };

  const statusText = useMemo(() => {
    if (!status) {
      return "Checking catalog status...";
    }
    if (status.state === "running") {
      const progress = status.target
        ? `${status.processed}/${status.target}`
        : `${status.processed} checked`;
      return `Refreshing catalog · ${progress} · ${status.last_album_count} valid albums`;
    }
    if (status.state === "error") {
      return `Refresh failed · ${status.last_album_count} valid albums`;
    }
    if (!status.last_album_count) {
      return "Initializing catalog...";
    }
    return `Ready · ${status.last_album_count} valid albums`;
  }, [status]);

  const compactStatus = useMemo(() => {
    if (!status) {
      return "Checking…";
    }
    if (status.state === "running") {
      return "Refreshing…";
    }
    if (status.state === "error") {
      return "Refresh failed";
    }
    if (!status.last_album_count) {
      return "Initializing…";
    }
    return "Ready";
  }, [status]);

  const handleReroll = () => {
    if (loading) {
      return;
    }
    void loadAlbum(selectedAge, true);
  };

  const handleAgeChange = (value: string) => {
    if (!value) {
      return;
    }
    const nextAge = value as AgeBucket;
    setSelectedAge(nextAge);
    void loadAlbum(nextAge, true);
  };

  const handleRefresh = async () => {
    setRefreshing(true);
    try {
      await refreshCatalog();
      toast.success("Catalog refresh started.");
    } catch {
      toast.error("Could not start catalog refresh.");
    } finally {
      setRefreshing(false);
    }
  };

  const controlsDisabled = !album;
  const refreshDisabled = refreshing || status?.state === "running";
  const selectedIndex = Math.max(
    0,
    AGE_OPTIONS.findIndex((option) => option.value === selectedAge)
  );

  return (
    <TooltipProvider>
      <div className="app-shell min-h-[100svh] px-4 pb-12 pt-6 md:pt-12">
        <div className="mx-auto flex w-full max-w-5xl flex-col gap-6 md:gap-7">
          <Accordion
            type="single"
            collapsible
            className="rounded-[var(--radius)] border border-[hsl(var(--border))] bg-white/70 shadow-sm backdrop-blur md:hidden"
          >
            <AccordionItem value="status">
              <AccordionTrigger className="text-sm">
                <span className="text-sm font-semibold">Die drei ???</span>
                <span className="flex items-center gap-2 text-xs text-[hsl(var(--muted-foreground))]">
                  <span
                    className={cn(
                      "h-2 w-2 rounded-full",
                      status?.state === "running"
                        ? "bg-amber-500"
                        : status?.state === "error"
                          ? "bg-red-500"
                          : "bg-emerald-500"
                    )}
                  />
                  <span>{compactStatus}</span>
                </span>
              </AccordionTrigger>
              <AccordionContent>
                <div className="flex flex-col gap-3 text-sm">
                  <p className="text-sm text-[hsl(var(--muted-foreground))]">
                    Roll a random episode, explore the timeline, and refresh the
                    catalog on demand.
                  </p>
                  <div className="flex flex-col gap-3 rounded-[var(--radius-inset)] border border-[hsl(var(--border))] bg-white/80 p-3">
                    <div className="flex items-center gap-2 text-sm text-[hsl(var(--muted-foreground))]">
                      <span
                        className={cn(
                          "h-2 w-2 rounded-full",
                          status?.state === "running"
                            ? "bg-amber-500"
                            : status?.state === "error"
                              ? "bg-red-500"
                              : "bg-emerald-500"
                        )}
                      />
                      <span>{statusText}</span>
                    </div>
                    <Button
                      variant="outline"
                      className="border-dashed"
                      onClick={handleRefresh}
                      disabled={refreshDisabled}
                    >
                      <RefreshCcw
                        className={cn(
                          "h-4 w-4",
                          refreshDisabled && "animate-spin"
                        )}
                      />
                      Refresh catalog
                    </Button>
                  </div>
                </div>
              </AccordionContent>
            </AccordionItem>
          </Accordion>

          <Card className="hidden border-[hsl(var(--border))] bg-white/75 backdrop-blur md:block">
            <CardHeader className="gap-4">
              <div className="flex flex-wrap items-center justify-between gap-4">
                <div>
                  <CardTitle className="headline text-2xl tracking-tight md:text-3xl">
                    Die drei ??? Album Viewer
                  </CardTitle>
                  <CardDescription className="mt-1 text-sm md:text-base">
                    Roll a random episode, explore the timeline, and refresh the catalog on demand.
                  </CardDescription>
                </div>
                <Tooltip>
                  <TooltipTrigger asChild>
                    <Button
                      variant="outline"
                      className="border-dashed"
                      onClick={handleRefresh}
                      disabled={refreshDisabled}
                    >
                      <RefreshCcw className={cn("h-4 w-4", refreshDisabled && "animate-spin")} />
                      Refresh
                    </Button>
                  </TooltipTrigger>
                  <TooltipContent>
                    {status?.state === "running"
                      ? "Refresh already running"
                      : "Rebuild the catalog from iTunes"}
                  </TooltipContent>
                </Tooltip>
              </div>
              <div className="flex items-center gap-2 text-sm text-[hsl(var(--muted-foreground))]">
                <span className={cn("h-2 w-2 rounded-full", status?.state === "running" ? "bg-amber-500" : status?.state === "error" ? "bg-red-500" : "bg-emerald-500")} />
                <span>{statusText}</span>
              </div>
            </CardHeader>
          </Card>

          <Card className="viewer-card flex min-h-[calc(100svh-16rem)] flex-col overflow-hidden border-[hsl(var(--border))] bg-white/80 backdrop-blur md:min-h-[520px]">
            <CardContent className="flex flex-1 flex-col gap-7 p-7 md:grid md:grid-cols-[minmax(0,1.1fr)_minmax(0,1fr)] md:gap-8 md:p-8">
              <div className="flex items-center justify-center">
                <div className="relative w-full max-w-xs md:max-w-sm">
                  <div
                    className={cn(
                      "cover-frame cover-sheen group aspect-square w-full overflow-hidden rounded-[calc(var(--radius)+6px)] bg-[hsl(var(--muted))]",
                      loading && "is-active",
                      loading && "opacity-90"
                    )}
                  >
                    {album ? (
                      <img
                        key={albumKey}
                        src={album.artwork_url}
                        alt={album.collection_name}
                        className={cn(
                          "album-enter h-full w-full object-cover transition-transform duration-500 ease-out group-hover:scale-[1.02]",
                          loading && "rerolling"
                        )}
                        loading="lazy"
                      />
                    ) : (
                      <Skeleton className="h-full w-full" />
                    )}
                  </div>
                  {loading ? (
                    <div className="absolute inset-0 grid place-items-center rounded-[var(--radius)] bg-white/30 backdrop-blur-sm">
                      <Loader2 className="h-8 w-8 animate-spin text-[hsl(var(--muted-foreground))]" />
                    </div>
                  ) : null}
                </div>
              </div>

              <div className="flex flex-col justify-center gap-5 md:gap-6">
                <div className="space-y-5 md:space-y-6">
                  <div className="relative min-h-[150px] md:min-h-[180px]">
                    <p className="text-xs uppercase tracking-[0.3em] text-[hsl(var(--muted-foreground))]">
                      Random Episode
                    </p>
                    <h2
                      className={cn(
                        "headline text-balance mt-2 text-[clamp(1.35rem,3.6vw,2.2rem)] leading-tight tracking-tight md:text-[clamp(1.8rem,2.4vw,2.6rem)]",
                        loading && "blur-[1.5px] opacity-60"
                      )}
                    >
                      {album?.collection_name ?? "Loading episode"}
                    </h2>
                    <div
                      className={cn(
                        "mt-3 flex flex-wrap items-center gap-3 text-sm text-[hsl(var(--muted-foreground))]",
                        loading && "blur-[1.5px] opacity-60"
                      )}
                    >
                      <span>{album?.year ?? "—"}</span>
                      {runtime ? <span>Runtime {runtime}</span> : null}
                    </div>
                    {loading ? (
                      <div className="pointer-events-none absolute inset-0 space-y-3 pt-6">
                        <Skeleton className="h-6 w-3/4" />
                        <Skeleton className="h-4 w-1/2" />
                      </div>
                    ) : null}
                  </div>
                  <Button asChild className="w-fit" disabled={!album}>
                    <a
                      href={album?.apple_music_url}
                      target="_blank"
                      rel="noreferrer"
                    >
                      <Music2 className="h-4 w-4" />
                      Open in Apple Music
                    </a>
                  </Button>
                </div>
              </div>
            </CardContent>
            <CardFooter className="mt-auto flex min-h-[96px] flex-col items-start gap-4 border-t border-[hsl(var(--border))] bg-[hsl(var(--muted))] py-4 md:flex-row md:items-center md:justify-between md:py-5">
              <div className="relative w-full max-w-xs md:max-w-none">
                <div
                  className="pointer-events-none absolute inset-1 z-0 rounded-[var(--radius-tight)] bg-[hsl(var(--card))] shadow transition-transform duration-200 ease-out"
                  style={{
                    width: `calc((100% - 0.5rem) / ${AGE_OPTIONS.length})`,
                    transform: `translateX(${selectedIndex * 100}%)`,
                  }}
                />
                <ToggleGroup
                  type="single"
                  value={selectedAge}
                  onValueChange={handleAgeChange}
                  className="grid w-full grid-cols-4 gap-1 rounded-[var(--radius-inset)] bg-[hsl(var(--muted))] p-1"
                >
                  {AGE_OPTIONS.map((option) => (
                    <ToggleGroupItem
                      key={option.value}
                      value={option.value}
                      className="relative z-10"
                    >
                      {option.label}
                    </ToggleGroupItem>
                  ))}
                </ToggleGroup>
              </div>
              <Button
                onClick={handleReroll}
                disabled={controlsDisabled}
                className="min-w-[9.5rem]"
              >
                <Shuffle className={cn("h-4 w-4", loading && "animate-spin")} />
                Reroll
              </Button>
            </CardFooter>
          </Card>
        </div>
      </div>
      <Toaster richColors position="top-right" />
    </TooltipProvider>
  );
}
