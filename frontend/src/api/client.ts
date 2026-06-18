export async function apiGet<T>(path: string): Promise<T> {
  const response = await fetch(path);
  if (!response.ok) {
    throw new Error(await response.text());
  }
  return response.json() as Promise<T>;
}

export async function apiPost<T>(path: string, body: unknown): Promise<T> {
  const response = await fetch(path, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body)
  });
  if (!response.ok) {
    throw new Error(await response.text());
  }
  return response.json() as Promise<T>;
}

export async function apiDelete(path: string): Promise<void> {
  const response = await fetch(path, {
    method: "DELETE"
  });
  if (!response.ok) {
    throw new Error(await response.text());
  }
}

export interface ApiDownloadResult {
  blob: Blob;
  filename: string;
}

export async function apiDownload(path: string): Promise<ApiDownloadResult> {
  const response = await fetch(path);
  if (!response.ok) {
    throw new Error(await response.text());
  }

  const disposition = response.headers.get("Content-Disposition") || "";
  const encodedFilename = disposition.match(/filename\*=UTF-8''([^;]+)/i)?.[1];
  const plainFilename = disposition.match(/filename="?([^";]+)"?/i)?.[1];
  return {
    blob: await response.blob(),
    filename: encodedFilename
      ? decodeURIComponent(encodedFilename)
      : plainFilename || "translation.docx"
  };
}

export async function apiUpload<T>(path: string, file: File): Promise<T> {
  const body = new FormData();
  body.append("file", file);

  const response = await fetch(path, {
    method: "POST",
    body
  });
  if (!response.ok) {
    throw new Error(await response.text());
  }
  return response.json() as Promise<T>;
}
