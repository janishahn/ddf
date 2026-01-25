export type AgeBucket = "old" | "medium" | "new" | "all";

export type Album = {
  collection_id: number;
  collection_name: string;
  artwork_url: string;
  release_date: string;
  apple_music_url: string;
  year: number;
  runtime_millis: number | null;
};

export type RandomAlbumResponse = {
  age: AgeBucket;
  album: Album;
  runtime_millis: number | null;
  runtime_str: string | null;
};

export type CatalogStatus = {
  state: "idle" | "running" | "error";
  processed: number;
  target: number;
  last_album_count: number;
  reason: string | null;
};

export async function fetchRandomAlbum(
  age: AgeBucket | undefined,
  reroll: boolean,
  signal?: AbortSignal
): Promise<RandomAlbumResponse> {
  const params = new URLSearchParams();
  if (age) {
    params.set("age", age);
  }
  if (reroll) {
    params.set("reroll", "true");
  }

  const url = `/api/albums/random${params.toString() ? `?${params.toString()}` : ""}`;
  const response = await fetch(url, {
    method: "GET",
    cache: "no-store",
    signal,
  });

  const payload = await response.json();
  if (!response.ok) {
    const errorMessage =
      typeof payload?.error === "string" ? payload.error : "request_failed";
    throw new Error(errorMessage);
  }

  return payload as RandomAlbumResponse;
}

export async function fetchCatalogStatus(): Promise<CatalogStatus> {
  const response = await fetch("/api/admin/catalog/status", {
    cache: "no-store",
  });

  if (!response.ok) {
    throw new Error("status_failed");
  }

  return (await response.json()) as CatalogStatus;
}

export async function refreshCatalog(): Promise<void> {
  const response = await fetch("/api/admin/catalog/refresh", {
    method: "POST",
  });

  if (!response.ok) {
    throw new Error("refresh_failed");
  }
}
