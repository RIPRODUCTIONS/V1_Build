import { Page, Request, Response } from "@playwright/test";

/** Resolves with the NEXT request whose URL contains the substring (case-sensitive). */
export function awaitNextRequest(page: Page, contains: string): Promise<Request> {
  return new Promise((resolve) => {
    const handler = (req: Request) => {
      if (req.url().includes(contains) && req.method() === 'GET') {
        page.off("request", handler);
        resolve(req);
      }
    };
    page.on("request", handler);
  });
}

/** Resolves with the NEXT response whose URL contains the substring, method is GET, and status is 200. */
export function awaitNextResponse(page: Page, contains: string): Promise<Response> {
  return page.waitForResponse((res) => {
    const req = res.request();
    return req.method() === 'GET' && res.status() === 200 && res.url().includes(contains);
  });
}
