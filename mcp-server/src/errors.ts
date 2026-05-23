export class BackendError extends Error {
  readonly httpStatus: number;
  readonly code: number | null;
  readonly details: unknown;

  constructor(
    message: string,
    options: {
      httpStatus?: number;
      code?: number | null;
      details?: unknown;
    } = {},
  ) {
    super(message);
    this.name = "BackendError";
    this.httpStatus = options.httpStatus ?? 500;
    this.code = options.code ?? null;
    this.details = options.details ?? null;
  }
}

const HTTP_HINTS: Record<number, string> = {
  400: "请检查请求参数是否正确。",
  401: "API Key 无效或已过期，请确认 API_KEY 环境变量配置正确。",
  403: "当前账号无权执行此操作。",
  404: "请求的资源不存在，或后端接口尚未实现。",
  405: "后端尚未实现该 HTTP 方法，请确认后端已更新至最新版本并重启。",
  409: "资源状态冲突，当前操作无法执行。",
  422: "业务规则校验未通过，请调整输入后重试。",
  429: "请求过于频繁，请稍后再试。",
  500: "后端服务内部错误，请稍后重试或联系管理员。",
  503: "后端依赖服务不可用，请确认数据库等服务已启动。",
};

export function friendlyHttpMessage(status: number, fallback?: string): string {
  return HTTP_HINTS[status] ?? fallback ?? `后端返回 HTTP ${status}，请查看后端日志获取详情。`;
}

export function formatBackendError(error: unknown): string {
  if (error instanceof BackendError) {
    const parts = [error.message];
    if (error.code !== null) {
      parts.push(`（业务码 ${error.code}）`);
    }
    if (error.details) {
      parts.push(`\n详情：${JSON.stringify(error.details, null, 2)}`);
    }
    return parts.join("");
  }

  if (error instanceof Error) {
    if (error.message.includes("fetch failed") || error.message.includes("ECONNREFUSED")) {
      return "无法连接后端服务。请确认 BACKEND_URL 正确且后端已启动（默认 http://localhost:8000）。";
    }
    return error.message;
  }

  return "发生未知错误，请重试或查看 MCP 服务日志。";
}

export function notImplementedMessage(feature: string, endpoint: string): string {
  return (
    `${feature} 所需的后端接口尚未实现。\n` +
    `需要后端提供：${endpoint}\n` +
    `当前 MCP 已预留该工具，待后端接口就绪后即可使用。`
  );
}
