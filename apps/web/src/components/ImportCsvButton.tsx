"use client";

declare global {
  interface Window {
    builder?: {
      financeUploadCsv?: () => Promise<{
        ok?: boolean;
        error?: string;
        result?: { parsed?: number };
      }>;
    };
  }
}

export default function ImportCsvButton() {
  return (
    <button
      className="ml-4 rounded bg-[var(--electron-blue)] text-white px-2 py-1"
      onClick={async () => {
        try {
          // @ts-ignore
          if (
            typeof window !== "undefined" &&
            window.builder?.financeUploadCsv
          ) {
            // @ts-ignore
            const resp = await window.builder.financeUploadCsv();
            alert(
              resp?.ok
                ? `Imported ${resp?.result?.parsed || 0} rows`
                : `Import failed: ${resp?.error}`,
            );
          } else {
            alert("Desktop integration not available");
          }
        } catch (e: any) {
          alert(String(e?.message || e));
        }
      }}
    >
      Import CSV
    </button>
  );
}
