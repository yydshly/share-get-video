// Video Test Cases Page

import { Link } from "react-router-dom";
import { SEED_TEST_CASES } from "../seedData";

const INPUT_TYPE_LABELS: Record<string, string> = {
  insight_card: "资讯卡片",
  article: "文章",
  emotional_content: "情绪内容",
  product_info: "产品信息",
  image: "图片",
  knowledge_content: "知识内容",
};

const PRIORITY_COLORS: Record<number, string> = {
  1: "#ef4444",
  2: "#f59e0b",
  3: "#10b981",
};

export default function VideoTestCasesPage() {
  return (
    <div style={{ padding: "2rem", maxWidth: "1000px", margin: "0 auto" }}>
      <div style={{ marginBottom: "2rem" }}>
        <h1 style={{ fontSize: "1.5rem", fontWeight: 700, marginBottom: "0.5rem" }}>
          测试用例
        </h1>
        <p style={{ color: "#64748b" }}>
          内置标准测试场景，用于验证视频生成方案的效果与适配性
        </p>
      </div>

      <div style={{ display: "flex", flexDirection: "column", gap: "1rem" }}>
        {SEED_TEST_CASES.map((tc) => (
          <div
            key={tc.id}
            style={{
              background: "white",
              border: "1px solid #e2e8f0",
              borderRadius: "12px",
              padding: "1.5rem",
            }}
          >
            <div style={{ display: "flex", alignItems: "flex-start", justifyContent: "space-between", marginBottom: "1rem" }}>
              <div>
                <div style={{ display: "flex", alignItems: "center", gap: "0.75rem", marginBottom: "0.25rem" }}>
                  <h3 style={{ fontSize: "1.1rem", fontWeight: 600 }}>{tc.name}</h3>
                  <span
                    style={{
                      background: "#fef2f2",
                      color: PRIORITY_COLORS[tc.recommendedPriority] ?? "#64748b",
                      border: `1px solid ${PRIORITY_COLORS[tc.recommendedPriority] ?? "#64748b"}30`,
                      borderRadius: "999px",
                      padding: "0.1rem 0.5rem",
                      fontSize: "0.75rem",
                    }}
                  >
                    优先级 {tc.recommendedPriority}
                  </span>
                </div>
                <p style={{ fontSize: "0.9rem", color: "#64748b" }}>{tc.description}</p>
              </div>
              <Link
                to={`/video-lab/advice?scenario=${tc.id}`}
                style={{
                  background: "#3b82f6",
                  color: "white",
                  textDecoration: "none",
                  borderRadius: "8px",
                  padding: "0.4rem 0.8rem",
                  fontSize: "0.85rem",
                  whiteSpace: "nowrap",
                }}
              >
                查看建议
              </Link>
            </div>

            <div style={{ display: "flex", flexWrap: "wrap", gap: "1rem", fontSize: "0.85rem" }}>
              <div>
                <span style={{ color: "#94a3b8" }}>输入类型：</span>
                <span style={{ color: "#475569" }}>{INPUT_TYPE_LABELS[tc.inputType] ?? tc.inputType}</span>
              </div>
              <div>
                <span style={{ color: "#94a3b8" }}>目标时长：</span>
                <span style={{ color: "#475569" }}>{tc.targetDurationSec}秒</span>
              </div>
              <div>
                <span style={{ color: "#94a3b8" }}>画面比例：</span>
                <span style={{ color: "#475569" }}>{tc.aspectRatio}</span>
              </div>
            </div>

            <div style={{ marginTop: "0.75rem" }}>
              <span style={{ fontSize: "0.8rem", color: "#94a3b8" }}>验证重点：</span>
              <div style={{ display: "flex", flexWrap: "wrap", gap: "0.4rem", marginTop: "0.4rem" }}>
                {tc.evaluationFocus.map((f) => (
                  <span
                    key={f}
                    style={{
                      background: "#f1f5f9",
                      color: "#475569",
                      borderRadius: "4px",
                      padding: "0.15rem 0.5rem",
                      fontSize: "0.8rem",
                    }}
                  >
                    {f}
                  </span>
                ))}
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
