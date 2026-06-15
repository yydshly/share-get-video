/**
 * RouteConfigPanel.tsx - 路线配置面板
 *
 * V0.3.7: Route-specific configuration
 *
 * 特性：
 * - 根据所选路线显示对应参数（不混在一起）
 * - 一键应用候选 preset
 * - 参数修改回调，父组件可获取最新 params
 */

import { useState, useCallback } from "react";
import {
  VideoRoutePreset,
  PillowParams,
  RemotionParams,
  AiAssetParams,
  getPresetForRoute,
  ROUTE_DISPLAY_NAMES,
  ROUTE_TAGLINES,
  isPillowRoute,
  isRemotionRoute,
  isAiAssetRoute,
} from "../presets/videoRoutePresets";

// ─── 基础输入组件 ────────────────────────────────────────────────────────────

function ColorInput({ label, value, onChange }: { label: string; value: string; onChange: (v: string) => void }) {
  return (
    <label style={{ fontSize: "0.72rem", color: "#64748b", display: "flex", alignItems: "center", gap: 4 }}>
      {label}
      <input type="color" value={value} onChange={(e) => onChange(e.target.value)}
        style={{ width: 28, height: 24, padding: 0, border: "none", cursor: "pointer" }} />
    </label>
  );
}

function SelectInput({ label, value, options, onChange }: {
  label: string; value: string;
  options: { value: string; label: string }[];
  onChange: (v: string) => void;
}) {
  return (
    <label style={{ fontSize: "0.72rem", color: "#64748b", display: "flex", alignItems: "center", gap: 4 }}>
      {label}
      <select value={value} onChange={(e) => onChange(e.target.value)}
        style={{ fontSize: "0.75rem", borderRadius: 4, border: "1px solid #e2e8f0", padding: "2px 4px" }}>
        {options.map((o) => <option key={o.value} value={o.value}>{o.label}</option>)}
      </select>
    </label>
  );
}

function BoolInput({ label, value, onChange }: { label: string; value: boolean; onChange: (v: boolean) => void }) {
  return (
    <label style={{ fontSize: "0.72rem", color: "#64748b", display: "flex", alignItems: "center", gap: 4, cursor: "pointer" }}>
      <input type="checkbox" checked={value} onChange={(e) => onChange(e.target.checked)} />
      {label}
    </label>
  );
}

function NumberInput({ label, value, min, max, step = 1, onChange, unit = "" }: {
  label: string; value: number; min: number; max: number; step?: number;
  onChange: (v: number) => void; unit?: string;
}) {
  return (
    <label style={{ fontSize: "0.72rem", color: "#64748b", display: "flex", alignItems: "center", gap: 4 }}>
      {label}
      <input type="number" min={min} max={max} step={step} value={value} onChange={(e) => onChange(Number(e.target.value))}
        style={{ width: 52, fontSize: "0.75rem", borderRadius: 4, border: "1px solid #e2e8f0", padding: "2px 4px" }} />
      {unit}
    </label>
  );
}

// ─── Pillow 参数面板 ─────────────────────────────────────────────────────────

function PillowConfigPanel({ params, onChange }: { params: PillowParams; onChange: (p: PillowParams) => void }) {
  const u = (k: keyof PillowParams, v: unknown) => onChange({ ...params, [k]: v });
  return (
    <div style={{ display: "flex", flexDirection: "column", gap: "0.6rem" }}>
      <div>
        <div style={{ fontSize: "0.72rem", fontWeight: 700, color: "#0ea5e9", marginBottom: "0.3rem" }}>数据与高亮</div>
        <div style={{ display: "flex", flexWrap: "wrap", gap: "0.6rem", alignItems: "center" }}>
          <BoolInput label="显示数据可视化" value={params.showDataViz} onChange={(v) => u("showDataViz", v)} />
          <BoolInput label="主题自适应" value={params.themeAdaptive} onChange={(v) => u("themeAdaptive", v)} />
        </div>
      </div>
      <div>
        <div style={{ fontSize: "0.72rem", fontWeight: 700, color: "#0ea5e9", marginBottom: "0.3rem" }}>排版</div>
        <div style={{ display: "flex", flexWrap: "wrap", gap: "0.6rem", alignItems: "center" }}>
          <SelectInput label="高亮模式" value={params.highlightMode}
            options={[{ value: "auto", label: "自动" }, { value: "numbers", label: "数字" }, { value: "none", label: "无" }]}
            onChange={(v) => u("highlightMode", v)} />
          <SelectInput label="对齐" value={params.contentAlign}
            options={[{ value: "top", label: "顶部" }, { value: "center", label: "居中" }]}
            onChange={(v) => u("contentAlign", v)} />
        </div>
      </div>
      <div>
        <div style={{ fontSize: "0.72rem", fontWeight: 700, color: "#0ea5e9", marginBottom: "0.3rem" }}>转场</div>
        <div style={{ display: "flex", flexWrap: "wrap", gap: "0.6rem", alignItems: "center" }}>
          <BoolInput label="启用转场" value={params.transitionEnabled} onChange={(v) => u("transitionEnabled", v)} />
          {params.transitionEnabled && (
            <NumberInput label="转场帧数" value={params.transitionFrames} min={0} max={8} onChange={(v) => u("transitionFrames", v)} />
          )}
        </div>
      </div>
      <div>
        <div style={{ fontSize: "0.72rem", fontWeight: 700, color: "#0ea5e9", marginBottom: "0.3rem" }}>配色</div>
        <div style={{ display: "flex", flexWrap: "wrap", gap: "0.6rem", alignItems: "center" }}>
          <ColorInput label="标题" value={params.titleColor} onChange={(v) => u("titleColor", v)} />
          <ColorInput label="正文" value={params.bodyColor} onChange={(v) => u("bodyColor", v)} />
          <ColorInput label="高亮" value={params.highlightColor} onChange={(v) => u("highlightColor", v)} />
        </div>
      </div>
    </div>
  );
}

// ─── Remotion 参数面板 ───────────────────────────────────────────────────────

function RemotionConfigPanel({ params, onChange }: { params: RemotionParams; onChange: (p: RemotionParams) => void }) {
  const u = (k: keyof RemotionParams, v: unknown) => onChange({ ...params, [k]: v });
  return (
    <div style={{ display: "flex", flexDirection: "column", gap: "0.6rem" }}>
      <div>
        <div style={{ fontSize: "0.72rem", fontWeight: 700, color: "#8b5cf6", marginBottom: "0.3rem" }}>数据与动效</div>
        <div style={{ display: "flex", flexWrap: "wrap", gap: "0.6rem", alignItems: "center" }}>
          <BoolInput label="显示数据可视化" value={params.showDataViz} onChange={(v) => u("showDataViz", v)} />
          <SelectInput label="指标动画" value={params.metricAnimation}
            options={[{ value: "countup_bar", label: "计数条" }, { value: "countup_number", label: "计数组" }, { value: "none", label: "无" }]}
            onChange={(v) => u("metricAnimation", v)} />
          <SelectInput label="动效强度" value={params.motionIntensity}
            options={[{ value: "low", label: "低" }, { value: "medium", label: "中" }, { value: "high", label: "高" }]}
            onChange={(v) => u("motionIntensity", v)} />
        </div>
      </div>
      <div>
        <div style={{ fontSize: "0.72rem", fontWeight: 700, color: "#8b5cf6", marginBottom: "0.3rem" }}>配色与排版</div>
        <div style={{ display: "flex", flexWrap: "wrap", gap: "0.6rem", alignItems: "center" }}>
          <ColorInput label="主题色" value={params.accentColor} onChange={(v) => u("accentColor", v)} />
          <ColorInput label="高亮" value={params.highlightColor} onChange={(v) => u("highlightColor", v)} />
          <NumberInput label="字号×" value={params.fontScale} min={0.8} max={1.5} step={0.05} onChange={(v) => u("fontScale", v)} />
          <BoolInput label="显示图标" value={params.showIcon} onChange={(v) => u("showIcon", v)} />
        </div>
      </div>
      <div>
        <div style={{ fontSize: "0.72rem", fontWeight: 700, color: "#8b5cf6", marginBottom: "0.3rem" }}>模板风格</div>
        <div style={{ display: "flex", flexWrap: "wrap", gap: "0.6rem", alignItems: "center" }}>
          <SelectInput label="封面" value={params.coverStyle}
            options={[{ value: "editorial", label: "编辑风" }, { value: "cinematic", label: "电影感" }, { value: "minimal", label: "极简" }]}
            onChange={(v) => u("coverStyle", v)} />
          <SelectInput label="概览" value={params.overviewStyle}
            options={[{ value: "timeline", label: "时间轴" }, { value: "grid", label: "网格" }, { value: "clean", label: "简洁" }]}
            onChange={(v) => u("overviewStyle", v)} />
          <SelectInput label="转场" value={params.transitionStyle}
            options={[{ value: "slide_fade", label: "滑动淡入" }, { value: "fade", label: "淡入" }, { value: "slide", label: "滑动" }]}
            onChange={(v) => u("transitionStyle", v)} />
        </div>
      </div>
    </div>
  );
}

// ─── AI Asset 参数面板 ───────────────────────────────────────────────────────

function AiAssetConfigPanel({ params, onChange }: { params: AiAssetParams; onChange: (p: AiAssetParams) => void }) {
  const u = (k: keyof AiAssetParams, v: unknown) => onChange({ ...params, [k]: v });
  return (
    <div style={{ display: "flex", flexDirection: "column", gap: "0.6rem" }}>
      <div>
        <div style={{ fontSize: "0.72rem", fontWeight: 700, color: "#10b981", marginBottom: "0.3rem" }}>数据与动效</div>
        <div style={{ display: "flex", flexWrap: "wrap", gap: "0.6rem", alignItems: "center" }}>
          <BoolInput label="显示数据可视化" value={params.showDataViz} onChange={(v) => u("showDataViz", v)} />
          <BoolInput label="Ken Burns" value={params.kenBurns} onChange={(v) => u("kenBurns", v)} />
        </div>
      </div>
      <div>
        <div style={{ fontSize: "0.72rem", fontWeight: 700, color: "#10b981", marginBottom: "0.3rem" }}>背景与卡片</div>
        <div style={{ marginBottom: "0.4rem" }}>
          <div style={{ fontSize: "0.72rem", color: "#64748b", marginBottom: 4 }}>AI 背景提示词</div>
          <textarea value={params.imageStyle} onChange={(e) => u("imageStyle", e.target.value)} rows={2}
            style={{ width: "100%", padding: "0.4rem", border: "1px solid #e2e8f0", borderRadius: 6, fontSize: "0.75rem", fontFamily: "monospace", boxSizing: "border-box", resize: "vertical" }} />
        </div>
        <div style={{ display: "flex", flexWrap: "wrap", gap: "0.6rem", alignItems: "center" }}>
          <NumberInput label="背景暗化" value={params.backgroundDarken} min={0} max={1} step={0.05} onChange={(v) => u("backgroundDarken", v)} />
          <NumberInput label="卡片透明度" value={params.cardOpacity} min={0} max={1} step={0.05} onChange={(v) => u("cardOpacity", v)} />
          <BoolInput label="卡片模糊" value={params.cardBlur} onChange={(v) => u("cardBlur", v)} />
        </div>
      </div>
      <div>
        <div style={{ fontSize: "0.72rem", fontWeight: 700, color: "#10b981", marginBottom: "0.3rem" }}>配色与排版</div>
        <div style={{ display: "flex", flexWrap: "wrap", gap: "0.6rem", alignItems: "center" }}>
          <ColorInput label="高亮" value={params.highlightColor} onChange={(v) => u("highlightColor", v)} />
          <SelectInput label="对齐" value={params.contentAlign}
            options={[{ value: "top", label: "顶部" }, { value: "center", label: "居中" }]}
            onChange={(v) => u("contentAlign", v)} />
        </div>
      </div>
    </div>
  );
}

// ─── 主组件 ──────────────────────────────────────────────────────────────────

export interface RouteConfigPanelProps {
  routeId: string;
  initialParams?: Record<string, unknown>;
  onParamsChange: (params: Record<string, unknown>) => void;
}

export default function RouteConfigPanel({ routeId, initialParams = {}, onParamsChange }: RouteConfigPanelProps) {
  const preset = getPresetForRoute(routeId);
  const displayName = ROUTE_DISPLAY_NAMES[routeId as keyof typeof ROUTE_DISPLAY_NAMES] ?? routeId;
  const tagline = ROUTE_TAGLINES[routeId as keyof typeof ROUTE_TAGLINES] ?? "";

  // 初始化参数：preset 默认值 + initialParams 覆盖
  const getInitialParams = (): Record<string, unknown> => {
    if (!preset) return { ...initialParams };
    return { ...preset.params, ...initialParams };
  };

  const [currentParams, setCurrentParams] = useState<Record<string, unknown>>(getInitialParams);

  const handleApplyPreset = useCallback(() => {
    if (!preset) return;
    const newParams = { ...preset.params };
    setCurrentParams(newParams);
    onParamsChange(newParams);
  }, [preset, onParamsChange]);

  const handleParamChange = useCallback(
    (params: Record<string, unknown>) => {
      setCurrentParams(params);
      onParamsChange(params);
    },
    [onParamsChange]
  );

  if (!preset) {
    return (
      <div style={{ padding: "1rem", background: "#f8fafc", borderRadius: 8, fontSize: "0.8rem", color: "#64748b" }}>
        未知路线: {routeId}
      </div>
    );
  }

  const accentColor = isPillowRoute(routeId) ? "#0ea5e9" : isRemotionRoute(routeId) ? "#8b5cf6" : "#10b981";

  return (
    <div style={{
      background: "white",
      border: `1px solid ${accentColor}30`,
      borderRadius: 12,
      padding: "1.25rem",
      display: "flex",
      flexDirection: "column",
      gap: "0.9rem",
    }}>
      {/* 路线标题区 */}
      <div style={{ display: "flex", alignItems: "flex-start", justifyContent: "space-between", gap: "1rem" }}>
        <div>
          <div style={{ fontSize: "0.85rem", fontWeight: 700, color: accentColor }}>{displayName} 配置</div>
          <div style={{ fontSize: "0.72rem", color: "#64748b", marginTop: 2 }}>{tagline}</div>
        </div>
        <button onClick={handleApplyPreset} style={{
          background: `${accentColor}15`,
          color: accentColor,
          border: `1px solid ${accentColor}40`,
          borderRadius: 6,
          padding: "0.3rem 0.75rem",
          fontSize: "0.75rem",
          cursor: "pointer",
          whiteSpace: "nowrap",
        }}>
          应用候选 preset
        </button>
      </div>

      {/* 路线能力标签 */}
      <div style={{ display: "flex", flexWrap: "wrap", gap: "0.4rem" }}>
        {preset.capabilities.map((cap) => (
          <span key={cap} style={{
            fontSize: "0.68rem",
            background: `${accentColor}15`,
            color: accentColor,
            borderRadius: 10,
            padding: "2px 8px",
          }}>
            {cap}
          </span>
        ))}
      </div>

      {/* 参数表单 */}
      <div style={{ borderTop: "1px solid #f1f5f9", paddingTop: "0.75rem" }}>
        {isPillowRoute(routeId) && (
          <PillowConfigPanel
            params={currentParams as unknown as PillowParams}
            onChange={(p) => handleParamChange(p as unknown as Record<string, unknown>)}
          />
        )}
        {isRemotionRoute(routeId) && (
          <RemotionConfigPanel
            params={currentParams as unknown as RemotionParams}
            onChange={(p) => handleParamChange(p as unknown as Record<string, unknown>)}
          />
        )}
        {isAiAssetRoute(routeId) && (
          <AiAssetConfigPanel
            params={currentParams as unknown as AiAssetParams}
            onChange={(p) => handleParamChange(p as unknown as Record<string, unknown>)}
          />
        )}
      </div>
    </div>
  );
}
