export interface McpConfig {
  backendUrl: string;
  apiKey: string;
  platformUserId: string;
}

function trimTrailingSlash(url: string): string {
  return url.replace(/\/+$/, "");
}

export function loadConfig(): McpConfig {
  const backendUrl = process.env.BACKEND_URL?.trim();
  const apiKey = process.env.API_KEY?.trim();
  const platformUserId = process.env.PLATFORM_USER_ID?.trim();

  const missing: string[] = [];
  if (!backendUrl) missing.push("BACKEND_URL");
  if (!apiKey) missing.push("API_KEY");
  if (!platformUserId) missing.push("PLATFORM_USER_ID");

  if (missing.length > 0) {
    throw new Error(
      `缺少必需的环境变量：${missing.join("、")}。请在 Cursor mcp.json 的 env 中配置，或在启动前 export 这些变量。`,
    );
  }

  return {
    backendUrl: trimTrailingSlash(backendUrl!),
    apiKey: apiKey!,
    platformUserId: platformUserId!,
  };
}
