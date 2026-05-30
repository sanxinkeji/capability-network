#!/usr/bin/env node
import { McpServer } from "@modelcontextprotocol/sdk/server/mcp.js";
import { StdioServerTransport } from "@modelcontextprotocol/sdk/server/stdio.js";
import { z } from "zod";

import { BackendClient } from "./backend.js";
import { loadConfig } from "./config.js";
import { formatBackendError } from "./errors.js";

function textResult(text: string, isError = false) {
  return {
    content: [{ type: "text" as const, text }],
    isError,
  };
}

function jsonResult(data: unknown) {
  return textResult(JSON.stringify(data, null, 2));
}

async function main() {
  const config = loadConfig();
  const backend = new BackendClient(config);

  const server = new McpServer({
    name: "capability-network",
    version: "0.1.0",
  });

  server.registerTool(
    "health",
    {
      title: "健康检查",
      description:
        "检查 MCP 配置与后端服务连通性。返回后端 /health 状态及当前 PLATFORM_USER_ID。",
      inputSchema: z.object({}),
    },
    async () => {
      try {
        const backendHealth = await backend.health();
        return jsonResult({
          mcp: "ok",
          platform_user_id: config.platformUserId,
          backend_url: config.backendUrl,
          backend: backendHealth,
        });
      } catch (error) {
        return textResult(
          JSON.stringify(
            {
              mcp: "ok",
              platform_user_id: config.platformUserId,
              backend_url: config.backendUrl,
              backend: "unreachable",
              error: formatBackendError(error),
            },
            null,
            2,
          ),
          true,
        );
      }
    },
  );

  server.registerTool(
    "search_offers",
    {
      title: "搜索市场供给",
      description:
        "浏览全平台已发布的能力供给（市场发现）。返回所有用户的 published 供给，不限于当前 API Key 所属用户。",
      inputSchema: z.object({
        category: z
          .string()
          .optional()
          .describe("分类筛选，如 design、development"),
        channel: z.enum(["human", "agent"]).optional().describe("渠道：human 或 agent"),
        page: z.number().int().min(1).optional().describe("页码，默认 1"),
        page_size: z
          .number()
          .int()
          .min(1)
          .max(100)
          .optional()
          .describe("每页条数，默认 20，最大 100"),
      }),
    },
    async (params) => {
      try {
        const data = await backend.searchOffers(params);
        return jsonResult(data);
      } catch (error) {
        return textResult(formatBackendError(error), true);
      }
    },
  );

  server.registerTool(
    "list_my_offers",
    {
      title: "我的能力供给",
      description:
        "列出当前 API Key 所属用户自己创建的能力供给，含 draft / published / paused 等全部状态。",
      inputSchema: z.object({
        category: z
          .string()
          .optional()
          .describe("分类筛选，如 design、development"),
        channel: z.enum(["human", "agent"]).optional().describe("渠道：human 或 agent"),
        status: z
          .enum(["draft", "published", "paused"])
          .optional()
          .describe("状态：draft、published、paused"),
        page: z.number().int().min(1).optional().describe("页码，默认 1"),
        page_size: z
          .number()
          .int()
          .min(1)
          .max(100)
          .optional()
          .describe("每页条数，默认 20，最大 100"),
      }),
    },
    async (params) => {
      try {
        const data = await backend.listMyOffers(params);
        return jsonResult(data);
      } catch (error) {
        return textResult(formatBackendError(error), true);
      }
    },
  );

  server.registerTool(
    "create_intent",
    {
      title: "创建能力需求",
      description: "创建一条能力需求（Intent）。budget_max 单位为分（如 10000 = 100 元）。",
      inputSchema: z.object({
        title: z.string().min(1).max(200).describe("需求标题"),
        description: z.string().min(1).describe("需求描述"),
        category: z.string().min(1).max(64).describe("分类"),
        channel: z.enum(["human", "agent"]).optional().describe("渠道，默认 human"),
        settlement: z
          .enum(["fiat", "points"])
          .optional()
          .describe("结算方式：human 对应 fiat，agent 对应 points"),
        budget_max: z.number().int().min(0).describe("预算上限（分）"),
        currency: z.string().length(3).optional().describe("货币代码，默认 CNY"),
        deadline: z
          .string()
          .optional()
          .describe("截止时间，ISO 8601 格式，如 2026-06-01T00:00:00Z"),
        acceptance_criteria: z
          .record(z.unknown())
          .optional()
          .describe("验收标准，JSON 对象"),
      }),
    },
    async (params) => {
      try {
        const body: Record<string, unknown> = { ...params };
        if (body.acceptance_criteria === undefined) {
          body.acceptance_criteria = {};
        }
        const data = await backend.createIntent(body);
        return jsonResult(data);
      } catch (error) {
        return textResult(formatBackendError(error), true);
      }
    },
  );

  server.registerTool(
    "run_matching",
    {
      title: "运行匹配",
      description: "对指定 Intent 运行匹配算法，返回推荐的能力供给候选列表。",
      inputSchema: z.object({
        intent_id: z.string().uuid().describe("Intent UUID"),
        top_n: z
          .number()
          .int()
          .min(1)
          .max(100)
          .optional()
          .describe("返回候选数量，默认 10"),
      }),
    },
    async (params) => {
      try {
        const data = await backend.runMatching(params);
        return jsonResult(data);
      } catch (error) {
        return textResult(formatBackendError(error), true);
      }
    },
  );

  server.registerTool(
    "join_auction",
    {
      title: "竞价报名命中",
      description:
        "Agent 对 agent 通道 Intent 报名参与竞价。至少 2 个参与者后买方可启动拍价。",
      inputSchema: z.object({
        intent_id: z.string().uuid().describe("Intent UUID"),
        offer_id: z.string().uuid().describe("Offer UUID"),
        match_log_id: z.string().uuid().optional().describe("匹配日志 UUID（可选）"),
      }),
    },
    async (params) => {
      try {
        const data = await backend.joinAuction(params);
        return jsonResult(data);
      } catch (error) {
        return textResult(formatBackendError(error), true);
      }
    },
  );

  server.registerTool(
    "submit_bid",
    {
      title: "竞价出价",
      description:
        "在 auctioning 状态的竞价室提交出价。amount_cents 须 ≤ intent 预算（分）。",
      inputSchema: z.object({
        auction_id: z.string().uuid().describe("Auction UUID"),
        amount_cents: z.number().int().min(1).describe("出价金额（分）"),
      }),
    },
    async (params) => {
      try {
        const data = await backend.submitBid(params);
        return jsonResult(data);
      } catch (error) {
        return textResult(formatBackendError(error), true);
      }
    },
  );

  server.registerTool(
    "create_deal",
    {
      title: "创建交易",
      description:
        "基于 Intent 与 Offer 创建交易（Deal）。需提供 intent_id + offer_id，或单独提供 match_log_id。",
      inputSchema: z
        .object({
          intent_id: z.string().uuid().optional().describe("Intent UUID"),
          offer_id: z.string().uuid().optional().describe("Offer UUID"),
          match_log_id: z.string().uuid().optional().describe("匹配日志 UUID（与 intent+offer 二选一）"),
        })
        .refine(
          (v) =>
            (v.intent_id !== undefined && v.offer_id !== undefined) !==
            (v.match_log_id !== undefined),
          {
            message: "请提供 intent_id + offer_id，或单独提供 match_log_id，二者不可同时使用。",
          },
        ),
    },
    async (params) => {
      try {
        const data = await backend.createDeal(params as Record<string, unknown>);
        return jsonResult(data);
      } catch (error) {
        return textResult(formatBackendError(error), true);
      }
    },
  );

  server.registerTool(
    "get_deal",
    {
      title: "查询交易",
      description: "根据 Deal ID 查询交易详情。",
      inputSchema: z.object({
        deal_id: z.string().uuid().describe("Deal UUID"),
      }),
    },
    async ({ deal_id }) => {
      try {
        const data = await backend.getDeal(deal_id);
        return jsonResult(data);
      } catch (error) {
        return textResult(formatBackendError(error), true);
      }
    },
  );

  server.registerTool(
    "list_deals",
    {
      title: "交易列表",
      description:
        "分页列出当前 API Key 所属用户参与的交易（作为买方或卖方），按创建时间降序。",
      inputSchema: z.object({
        page: z.number().int().min(1).optional().describe("页码，默认 1"),
        page_size: z
          .number()
          .int()
          .min(1)
          .max(100)
          .optional()
          .describe("每页条数，默认 20，最大 100"),
      }),
    },
    async (params) => {
      try {
        const data = await backend.listDeals(params);
        return jsonResult(data);
      } catch (error) {
        return textResult(formatBackendError(error), true);
      }
    },
  );

  server.registerTool(
    "pay_deal",
    {
      title: "支付交易",
      description:
        "买方支付指定交易并冻结资金。仅 `pending` 状态的 Deal 可支付；需当前用户为买方且钱包余额充足。",
      inputSchema: z.object({
        deal_id: z.string().uuid().describe("Deal UUID"),
      }),
    },
    async ({ deal_id }) => {
      try {
        const data = await backend.payDeal(deal_id);
        return jsonResult(data);
      } catch (error) {
        return textResult(formatBackendError(error), true);
      }
    },
  );

  server.registerTool(
    "deliver_deal",
    {
      title: "交付交易",
      description:
        "卖方提交交付物，将 `in_progress` 状态的交易转为 `delivered`。需提供 text 或 payload_url 至少一项。",
      inputSchema: z.object({
        deal_id: z.string().uuid().describe("Deal UUID"),
        text: z.string().optional().describe("交付说明或文本结果"),
        payload_url: z.string().url().optional().describe("交付物 URL"),
      }),
    },
    async ({ deal_id, text, payload_url }) => {
      try {
        const body: Record<string, string> = {};
        if (text !== undefined) body.text = text;
        if (payload_url !== undefined) body.payload_url = payload_url;
        const data = await backend.deliverDeal(deal_id, body);
        return jsonResult(data);
      } catch (error) {
        return textResult(formatBackendError(error), true);
      }
    },
  );

  server.registerTool(
    "list_deal_messages",
    {
      title: "订单聊天消息",
      description:
        "列出指定订单的会话消息（支付后聊天）。当前用户须为买方或卖方。按时间升序返回。",
      inputSchema: z.object({
        deal_id: z.string().uuid().describe("Deal UUID"),
      }),
    },
    async ({ deal_id }) => {
      try {
        const data = await backend.listDealMessages(deal_id);
        return jsonResult(data);
      } catch (error) {
        return textResult(formatBackendError(error), true);
      }
    },
  );

  server.registerTool(
    "post_deal_message",
    {
      title: "发送订单聊天消息",
      description:
        "在订单会话中发送消息。买方/卖方可沟通需求；卖方 API Key（OpenClaw）以 agent 身份发言。",
      inputSchema: z.object({
        deal_id: z.string().uuid().describe("Deal UUID"),
        body: z.string().min(1).max(8000).describe("消息正文"),
      }),
    },
    async ({ deal_id, body }) => {
      try {
        const data = await backend.postDealMessage(deal_id, { body });
        return jsonResult(data);
      } catch (error) {
        return textResult(formatBackendError(error), true);
      }
    },
  );

  server.registerTool(
    "create_offer",
    {
      title: "创建能力供给",
      description:
        "创建一条能力供给（Offer），初始状态为 draft。price_cents 单位为分（如 100 = 1 元）。",
      inputSchema: z.object({
        title: z.string().min(1).max(200).describe("供给标题"),
        description: z.string().min(1).describe("供给描述"),
        category: z.string().min(1).max(64).describe("分类"),
        channel: z.enum(["human", "agent"]).describe("渠道：human 或 agent"),
        billing_model: z
          .enum(["per_use", "per_query", "per_hour"])
          .describe("计费模型"),
        price_cents: z.number().int().min(0).describe("价格（分）"),
        currency: z.string().length(3).optional().describe("货币代码，默认 CNY"),
        delivery_description: z.string().optional().describe("交付说明"),
      }),
    },
    async (params) => {
      try {
        const data = await backend.createOffer(params as Record<string, unknown>);
        return jsonResult(data);
      } catch (error) {
        return textResult(formatBackendError(error), true);
      }
    },
  );

  server.registerTool(
    "publish_offer",
    {
      title: "发布能力供给",
      description: "将 draft 状态的 Offer 发布到市场（published）。仅供给所有者可操作。",
      inputSchema: z.object({
        offer_id: z.string().uuid().describe("Offer UUID"),
      }),
    },
    async ({ offer_id }) => {
      try {
        const data = await backend.publishOffer(offer_id);
        return jsonResult(data);
      } catch (error) {
        return textResult(formatBackendError(error), true);
      }
    },
  );

  server.registerTool(
    "wallet_balance",
    {
      title: "钱包余额",
      description: "查询当前 API Key 所属用户的钱包余额（可用、冻结、不可提现点数）。",
      inputSchema: z.object({}),
    },
    async () => {
      try {
        const data = await backend.walletBalance();
        return jsonResult(data);
      } catch (error) {
        return textResult(formatBackendError(error), true);
      }
    },
  );

  server.registerTool(
    "create_deposit_order",
    {
      title: "创建充值订单",
      description: "创建微信/支付宝充值订单，返回 pay_url 供用户扫码支付。amount_cents 单位为分。",
      inputSchema: z.object({
        amount_cents: z.number().int().min(1).describe("充值金额（分）"),
        channel: z.enum(["wechat", "alipay"]).describe("支付渠道"),
      }),
    },
    async ({ amount_cents, channel }) => {
      try {
        const data = await backend.createDepositOrder(amount_cents, channel);
        return jsonResult(data);
      } catch (error) {
        return textResult(formatBackendError(error), true);
      }
    },
  );

  server.registerTool(
    "confirm_deal",
    {
      title: "确认收货",
      description: "买方确认已交付订单，完成结算。仅 delivered 状态可确认。",
      inputSchema: z.object({
        deal_id: z.string().uuid().describe("Deal UUID"),
      }),
    },
    async ({ deal_id }) => {
      try {
        const data = await backend.confirmDeal(deal_id);
        return jsonResult(data);
      } catch (error) {
        return textResult(formatBackendError(error), true);
      }
    },
  );

  server.registerTool(
    "parse_intent",
    {
      title: "AI 解析需求",
      description: "用自然语言解析需求，返回标题、类目、预算等结构化字段。",
      inputSchema: z.object({
        text: z.string().min(1).describe("自然语言需求描述"),
      }),
    },
    async ({ text }) => {
      try {
        const data = await backend.parseIntent({ text });
        return jsonResult(data);
      } catch (error) {
        return textResult(formatBackendError(error), true);
      }
    },
  );

  server.registerTool(
    "list_intents",
    {
      title: "我的需求列表",
      description: "列出当前用户创建的需求。",
      inputSchema: z.object({}),
    },
    async () => {
      try {
        const data = await backend.listIntents();
        return jsonResult(data);
      } catch (error) {
        return textResult(formatBackendError(error), true);
      }
    },
  );

  const transport = new StdioServerTransport();
  await server.connect(transport);
}

main().catch((error) => {
  console.error(error instanceof Error ? error.message : error);
  process.exit(1);
});
