// Send every visit to the one address that Cloudflare Access protects.
// Covers the .pages.dev address (and preview builds) and www.
const HOME = "dailydesk.win";

export async function onRequest(context) {
  const url = new URL(context.request.url);
  const host = url.hostname;
  if (host === "www." + HOME || host.endsWith(".pages.dev")) {
    url.protocol = "https:";
    url.hostname = HOME;
    url.port = "";
    return Response.redirect(url.toString(), 301);
  }
  return context.next();
}
