import type { McpConfig } from "./config.js";
import { BackendError, friendlyHttpMessage } from "./errors.js";

interface ApiEnvelope {
  code?: number;
  message?: string;
  data?: unknown;
  errors?: Array<{ field?: string; detail?: string }>;
}

export class BackendClient {
  constructor(private readonly config: McpConfig) {}

  private authHeaders(): Record<string, string> {
    return {
      Authorization: `Bearer ${this.config.apiKey}`,
      Accept: "application/json",
      "Content-Type": "application/json",
    };
  }

  async health(): Promise<Record<string, unknown>> {
    const response = await fetch(`${this.config.backendUrl}/health`);
    if (!response.ok) {
      throw new BackendError(friendlyHttpMessage(response.status, "健康检查失败。"), {
        httpStatus: response.status,
      });
    }
    return (await response.json()) as Record<string, unknown>;
  }

  async searchOffers(params: {
    category?: string;
    channel?: string;
    page?: number;
    page_size?: number;
  }): Promise<unknown> {
    const query = new URLSearchParams();
    if (params.category) query.set("category", params.category);
    if (params.channel) query.set("channel", params.channel);
    if (params.page) query.set("page", String(params.page));
    if (params.page_size) query.set("page_size", String(params.page_size));

    const qs = query.toString();
    const path = `/api/v1/offers/marketplace${qs ? `?${qs}` : ""}`;
    return this.request("GET", path);
  }

  async listMyOffers(params: {
    category?: string;
    channel?: string;
    status?: string;
    page?: number;
    page_size?: number;
  }): Promise<unknown> {
    const query = new URLSearchParams();
    if (params.category) query.set("category", params.category);
    if (params.channel) query.set("channel", params.channel);
    if (params.status) query.set("status", params.status);
    if (params.page) query.set("page", String(params.page));
    if (params.page_size) query.set("page_size", String(params.page_size));

    const qs = query.toString();
    const path = `/api/v1/offers${qs ? `?${qs}` : ""}`;
    return this.request("GET", path);
  }

  async createIntent(body: Record<string, unknown>): Promise<unknown> {
    return this.request("POST", "/api/v1/intents", body);
  }

  async runMatching(body: { intent_id: string; top_n?: number }): Promise<unknown> {
    return this.request("POST", "/api/v1/matching/run", body);
  }

  async createDeal(body: Record<string, unknown>): Promise<unknown> {
    return this.request("POST", "/api/v1/deals", body);
  }

  async getDeal(dealId: string): Promise<unknown> {
    return this.request("GET", `/api/v1/deals/${dealId}`);
  }

  async listDeals(params: {
    page?: number;
    page_size?: number;
  }): Promise<unknown> {
    const query = new URLSearchParams();
    if (params.page) query.set("page", String(params.page));
    if (params.page_size) query.set("page_size", String(params.page_size));

    const qs = query.toString();
    const path = `/api/v1/deals${qs ? `?${qs}` : ""}`;
    return this.request("GET", path);
  }

  async payDeal(dealId: string): Promise<unknown> {
    return this.request("POST", `/api/v1/deals/${dealId}/pay`);
  }

  async deliverDeal(
    dealId: string,
    body: { text?: string; payload_url?: string },
  ): Promise<unknown> {
    return this.request("POST", `/api/v1/deals/${dealId}/deliver`, body);
  }

  async createOffer(body: Record<string, unknown>): Promise<unknown> {
    return this.request("POST", "/api/v1/offers", body);
  }

  async publishOffer(offerId: string): Promise<unknown> {
    return this.request("POST", `/api/v1/offers/${offerId}/publish`);
  }

  async walletBalance(): Promise<unknown> {
    return this.request("GET", "/api/v1/wallets/me");
  }

  async createDepositOrder(amountCents: number, channel: "wechat" | "alipay"): Promise<unknown> {
    return this.request("POST", "/api/v1/wallets/deposit-orders", {
      amount_cents: amountCents,
      channel,
    });
  }

  async walletLedger(params: { page?: number; page_size?: number }): Promise<unknown> {
    const query = new URLSearchParams();
    if (params.page) query.set("page", String(params.page));
    if (params.page_size) query.set("page_size", String(params.page_size));
    const qs = query.toString();
    return this.request("GET", `/api/v1/wallets/ledger${qs ? `?${qs}` : ""}`);
  }

  async confirmDeal(dealId: string): Promise<unknown> {
    return this.request("POST", `/api/v1/deals/${dealId}/confirm`, {});
  }

  async parseIntent(body: { text: string }): Promise<unknown> {
    return this.request("POST", "/api/v1/intents/parse", body);
  }

  async joinAuction(body: {
    intent_id: string;
    offer_id: string;
    match_log_id?: string;
  }): Promise<unknown> {
    return this.request("POST", `/api/v1/intents/${body.intent_id}/auction/join`, {
      offer_id: body.offer_id,
      match_log_id: body.match_log_id,
    });
  }

  async submitBid(body: { auction_id: string; amount_cents: number }): Promise<unknown> {
    return this.request("POST", `/api/v1/auctions/${body.auction_id}/bid`, {
      amount_cents: body.amount_cents,
    });
  }

  async listIntents(): Promise<unknown> {
    return this.request("GET", "/api/v1/intents");
  }

  private async request(
    method: string,
    path: string,
    body?: Record<string, unknown>,
  ): Promise<unknown> {
    const url = `${this.config.backendUrl}${path}`;
    let response: Response;

    try {
      response = await fetch(url, {
        method,
        headers: this.authHeaders(),
        body: body === undefined ? undefined : JSON.stringify(body),
      });
    } catch (cause) {
      const message =
        cause instanceof Error && cause.message.includes("fetch failed")
          ? "无法连接后端服务。请确认 BACKEND_URL 正确且后端已启动。"
          : "请求后端时发生网络错误。";
      throw new BackendError(message, { httpStatus: 0, details: String(cause) });
    }

    const text = await response.text();
    let payload: ApiEnvelope | null = null;

    if (text) {
      try {
        payload = JSON.parse(text) as ApiEnvelope;
      } catch {
        if (!response.ok) {
          throw new BackendError(friendlyHttpMessage(response.status), {
            httpStatus: response.status,
            details: text.slice(0, 500),
          });
        }
      }
    }

    if (payload && typeof payload.code === "number") {
      if (payload.code !== 0) {
        const fieldErrors =
          payload.errors?.map((e) => `${e.field ?? "?"}: ${e.detail ?? ""}`).join("; ") ?? "";
        const detail = fieldErrors ? ` ${fieldErrors}` : "";
        throw new BackendError(`${payload.message ?? "请求失败"}${detail}`.trim(), {
          httpStatus: response.status,
          code: payload.code,
          details: payload.errors ?? null,
        });
      }
      return payload.data;
    }

    if (!response.ok) {
      throw new BackendError(friendlyHttpMessage(response.status), {
        httpStatus: response.status,
        details: payload ?? text.slice(0, 500),
      });
    }

    return payload?.data ?? payload ?? null;
  }
}
