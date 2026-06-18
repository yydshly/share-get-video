from app.video_lab.services.information_structure_service import (
    generate_information_structure,
    serialize_for_visual_compose,
    _derive_item_title_from_description,
    _split_report_item_blocks,
)


REPORT_INPUT = """今日AI前沿呈现多条并行进展线索：多语言NLP在低资源方言、科学事实检测等领域取得突破，阿尔及利亚方言谣言检测混合框架F1达0.84；AI评估体系向多维化和精细化演进，购物推理、长期搜索、立场复杂度等新基准揭示主流模型显著短板；安全对齐方面，主动调查评审、欺骗检测等新范式推动可扩展监督研究；企业级AI落地加速，Anthropic与TCS/DXC合作进入受监管行业，DeepMind千万美元投入多智能体安全研究。整体来看，研究重心正从单一性能提升转向可信性、可靠性和跨文化鲁棒性的综合评估。

科学研究评审实现"主动调查"突破：ProReviewer系统将评审建模为马尔可夫决策过程，在五个质量维度超越提示工程方法39%，为AI辅助学术评审提供新范式。

欺骗检测新范式：RogueAI将信任问题转化为"审问游戏"，玩家需在有限回合内识别人机混合对话中的欺骗者，为可扩展监督和LLM欺骗检测开辟新思路。

购物AI助手全面落后主流模型：Shopping Reasoning Bench测评发现GPT、Claude、Gemini系列通过率仅57-77%，多轮场景下所有模型表现更差，暴露复杂推理短板。

立场检测揭示"相变"规律：SICI复杂度指数发现LLM错误模式随复杂度呈现三阶段相变——低复杂度过度归因、中等复杂度不稳定、高复杂度集中无立场，为立场检测提供诊断工具。

AI同行评审存在"展示层"攻击漏洞：攻击者可仅修改摘要措辞、相关工作定位等展示层面内容，实现75.1%攻击成功率，对高校AI审稿政策提出警示。

企业级AI加速进入受监管行业：Anthropic与TCS、DXC建立全球联盟，Claude进入银行、航空等高合规要求领域，DeepMind宣布千万美元多智能体安全研究投资。"""


REPORT_INPUT_WITH_EVIDENCE = """今日AI前沿呈现多条并行进展线索：多语言NLP、AI评估、安全对齐和企业级AI并行推进。整体来看，研究重心转向可信性、可靠性和跨文化鲁棒性。

科学研究评审实现"主动调查"突破：ProReviewer系统将评审建模为马尔可夫决策过程。
依据：依据 1

欺骗检测新范式：RogueAI将信任问题转化为"审问游戏"。
依据：依据 2

购物AI助手全面落后主流模型：Shopping Reasoning Bench测评发现主流模型仍有短板。
依据：依据 3

立场检测揭示"相变"规律：SICI复杂度指数发现LLM错误模式随复杂度呈现三阶段相变。
依据：依据 4

AI同行评审存在"展示层"攻击漏洞：攻击者可仅修改展示层内容实现攻击。
依据：依据 5

企业级AI加速进入受监管行业：Anthropic与TCS、DXC建立全球联盟。
依据：依据 6"""


REPORT_INPUT_SINGLE_NEWLINE_ITEMS = """今日AI前沿呈现多条并行进展线索：多语言NLP在低资源方言、科学事实检测等领域取得突破，阿尔及利亚方言谣言检测混合框架F1达0.84；AI评估体系向多维化和精细化演进，购物推理、长期搜索、立场复杂度等新基准揭示主流模型显著短板；安全对齐方面，主动调查评审、欺骗检测等新范式推动可扩展监督研究；企业级AI落地加速，Anthropic与TCS/DXC合作进入受监管行业，DeepMind千万美元投入多智能体安全研究。整体来看，研究重心正从单一性能提升转向可信性、可靠性和跨文化鲁棒性的综合评估。

科学研究评审实现"主动调查"突破：ProReviewer系统将评审建模为马尔可夫决策过程，在五个质量维度超越提示工程方法39%，为AI辅助学术评审提供新范式。
欺骗检测新范式：RogueAI将信任问题转化为"审问游戏"，玩家需在有限回合内识别人机混合对话中的欺骗者，为可扩展监督和LLM欺骗检测开辟新思路。
购物AI助手全面落后主流模型：Shopping Reasoning Bench测评发现GPT、Claude、Gemini系列通过率仅57-77%，多轮场景下所有模型表现更差，暴露复杂推理短板。
立场检测揭示"相变"规律：SICI复杂度指数发现LLM错误模式随复杂度呈现三阶段相变——低复杂度过度归因、中等复杂度不稳定、高复杂度集中无立场，为立场检测提供诊断工具。
AI同行评审存在"展示层"攻击漏洞：攻击者可仅修改摘要措辞、相关工作定位等展示层面内容，实现75.1%攻击成功率，对高校AI审稿政策提出警示。
企业级AI加速进入受监管行业：Anthropic与TCS、DXC建立全球联盟，Claude进入银行、航空等高合规要求领域，DeepMind宣布千万美元多智能体安全研究投资。"""


REPORT_INPUT_SINGLE_NEWLINE_WITH_EVIDENCE = """今日AI前沿呈现多条并行进展线索：多语言NLP在低资源方言、科学事实检测等领域取得突破，阿尔及利亚方言谣言检测混合框架F1达0.84；AI评估体系向多维化和精细化演进，购物推理、长期搜索、立场复杂度等新基准揭示主流模型显著短板；安全对齐方面，主动调查评审、欺骗检测等新范式推动可扩展监督研究；企业级AI落地加速，Anthropic与TCS/DXC合作进入受监管行业，DeepMind千万美元投入多智能体安全研究。整体来看，研究重心正从单一性能提升转向可信性、可靠性和跨文化鲁棒性的综合评估。

科学研究评审实现"主动调查"突破：ProReviewer系统将评审建模为马尔可夫决策过程，在五个质量维度超越提示工程方法39%，为AI辅助学术评审提供新范式。
依据：依据 1
欺骗检测新范式：RogueAI将信任问题转化为"审问游戏"，玩家需在有限回合内识别人机混合对话中的欺骗者，为可扩展监督和LLM欺骗检测开辟新思路。
依据：依据 1
购物AI助手全面落后主流模型：Shopping Reasoning Bench测评发现GPT、Claude、Gemini系列通过率仅57-77%，多轮场景下所有模型表现更差，暴露复杂推理短板。
依据：依据 1
立场检测揭示"相变"规律：SICI复杂度指数发现LLM错误模式随复杂度呈现三阶段相变——低复杂度过度归因、中等复杂度不稳定、高复杂度集中无立场，为立场检测提供诊断工具。
依据：依据 1
AI同行评审存在"展示层"攻击漏洞：攻击者可仅修改摘要措辞、相关工作定位等展示层面内容，实现75.1%攻击成功率，对高校AI审稿政策提出警示。
依据：依据 1
企业级AI加速进入受监管行业：Anthropic与TCS、DXC建立全球联盟，Claude进入银行、航空等高合规要求领域，DeepMind宣布千万美元多智能体安全研究投资。
依据：依据 1 依据 2 依据 3"""


def build_report_structure(**overrides):
    params = {
        "compression_mode": "strict",
        "target_point_count": "all",
        "include_overview": True,
        "include_conclusion": True,
        "input_profile": "report_overview_items",
    }
    params.update(overrides)
    return generate_information_structure(REPORT_INPUT, **params)


def build_single_newline_structure(content=REPORT_INPUT_SINGLE_NEWLINE_ITEMS, **overrides):
    params = {
        "compression_mode": "strict",
        "target_point_count": "all",
        "include_overview": True,
        "include_conclusion": True,
        "input_profile": "report_overview_items",
    }
    params.update(overrides)
    return generate_information_structure(content, **params)


def test_report_profile_title_does_not_take_over_overview_when_body_is_provided():
    result = generate_information_structure(
        "今日 AI 前沿速递\n\nSHOULD_NOT_BE_USED",
        title="今日 AI 前沿速递",
        body=REPORT_INPUT_SINGLE_NEWLINE_ITEMS,
        compression_mode="strict",
        target_point_count="all",
        input_profile="report_overview_items",
    )
    assert result["overview"]["summary"] == REPORT_INPUT_SINGLE_NEWLINE_ITEMS.split("\n\n", 1)[0]
    assert result["overview"]["summary"] != "今日 AI 前沿速递"
    assert result["metadata"]["title"] == "今日 AI 前沿速递"


def test_report_profile_body_first_paragraph_does_not_enter_items_with_title_body():
    result = generate_information_structure(
        "今日 AI 前沿速递",
        title="今日 AI 前沿速递",
        body=REPORT_INPUT_SINGLE_NEWLINE_ITEMS,
        compression_mode="strict",
        target_point_count="all",
        input_profile="report_overview_items",
    )
    item_text = "\n".join(item["title"] + item["description"] for item in result["items"])
    assert "今日AI前沿呈现多条并行进展线索" not in item_text


def test_report_profile_single_newline_six_items_without_evidence():
    result = build_single_newline_structure()
    assert result["stats"]["detectedItemCount"] == 6
    assert result["stats"]["selectedItemCount"] == 6
    assert all(item["title"] for item in result["items"])


def test_report_profile_single_newline_six_items_with_evidence():
    result = build_single_newline_structure(REPORT_INPUT_SINGLE_NEWLINE_WITH_EVIDENCE)
    assert result["stats"]["detectedItemCount"] == 6
    assert result["stats"]["selectedItemCount"] == 6
    assert result["items"][0]["evidence"] == ["依据 1"]
    assert result["items"][-1]["evidence"] == ["依据 1 依据 2 依据 3"]
    assert all(item["title"] != "依据" for item in result["items"])


def test_report_profile_first_paragraph_is_overview():
    result = build_report_structure()
    overview = result["overview"]
    assert overview["summary"] == REPORT_INPUT.split("\n\n", 1)[0]
    assert overview["title"]


def test_report_profile_first_paragraph_does_not_enter_items():
    result = build_report_structure()
    item_text = "\n".join(item["title"] + item["description"] for item in result["items"])
    assert "今日AI前沿呈现多条并行进展线索" not in item_text
    assert "多语言NLP在低资源方言" not in result["items"][0]["title"]


def test_report_profile_later_title_colon_paragraphs_become_six_items():
    result = build_report_structure()
    assert result["stats"]["detectedItemCount"] == 6
    assert len(result["items"]) == 6
    assert result["items"][0]["title"] == '科学研究评审实现"主动调查"突破'
    assert "ProReviewer系统" in result["items"][0]["description"]


def test_report_profile_item_titles_are_not_empty():
    result = build_report_structure()
    assert all(item["title"] for item in result["items"])


def test_report_profile_evidence_attaches_to_previous_item_not_item():
    result = generate_information_structure(
        REPORT_INPUT_WITH_EVIDENCE,
        compression_mode="strict",
        target_point_count="all",
        include_overview=True,
        include_conclusion=True,
        input_profile="report_overview_items",
    )
    assert result["stats"]["detectedItemCount"] == 6
    assert len(result["items"]) == 6
    assert result["items"][0]["evidence"] == ["依据 1"]
    assert all(item["title"] != "依据" for item in result["items"])


def test_report_profile_strict_all_selects_all_detected_items():
    result = build_report_structure()
    assert result["stats"]["detectedItemCount"] == 6
    assert result["stats"]["selectedItemCount"] == 6
    assert result["stats"]["droppedItemCount"] == 0


def test_report_profile_brief_selects_three_but_detects_six():
    result = build_report_structure(compression_mode="brief", target_point_count="auto")
    assert result["stats"]["detectedItemCount"] == 6
    assert result["stats"]["selectedItemCount"] == 3
    assert result["stats"]["droppedItemCount"] == 3


def test_report_profile_conclusion_does_not_become_item():
    result = build_report_structure()
    item_text = "\n".join(item["title"] + item["description"] for item in result["items"])
    assert "整体来看" not in item_text
    assert result["conclusion"]["text"] == "" or "整体来看" in result["conclusion"]["text"]


def test_auto_profile_keeps_existing_service_behavior_available():
    result = generate_information_structure(
        REPORT_INPUT,
        compression_mode="strict",
        target_point_count="all",
        input_profile="auto",
    )
    assert result["inputProfile"] == "auto"
    assert "stats" in result
    assert isinstance(result["items"], list)


# ─── V1.2: No-title report items ────────────────────────────────────────────────


class TestNoTitleReportItems:
    """Tests for report items without explicit 'title：description' formatting."""

    NO_TITLE_REPORT = """今日 AI 前沿速览：多个模型和产品方向出现更新。

OpenAI 发布新模型，推理能力提升，但成本和调用稳定性仍需要观察。
依据：官方公告

Claude Code 新增能力，开发者可以更方便地完成代码修改和测试。
依据：产品文档"""

    MIXED_REPORT = """今日 AI 前沿速览：多个模型和产品方向出现更新。

模型发布：OpenAI 发布新模型，推理能力提升，但成本仍需观察。
依据：官方公告

Claude Code 新增能力，开发者可以更方便地完成代码修改和测试。
依据：产品文档"""

    # Two blank-line-separated paragraphs: overview + one no-title item
    SINGLE_PARAGRAPH_NO_TITLE = """今日 AI 前沿速览。

OpenAI 发布新模型，推理能力提升，但成本仍需观察。"""

    def test_no_title_report_detects_two_items(self):
        """No-title paragraphs should each become a separate item."""
        result = generate_information_structure(
            self.NO_TITLE_REPORT,
            compression_mode="strict",
            target_point_count="all",
            input_profile="report_overview_items",
        )
        assert result["stats"]["detectedItemCount"] == 2, (
            f"Expected 2 items, got {result['stats']['detectedItemCount']}: "
            f"{[item['title'] for item in result['items']]}"
        )

    def test_no_title_items_have_auto_generated_title(self):
        """No-title items should have auto-generated titles."""
        result = generate_information_structure(
            self.NO_TITLE_REPORT,
            compression_mode="strict",
            target_point_count="all",
            input_profile="report_overview_items",
        )
        for item in result["items"]:
            assert item.get("title"), f"Item missing title: {item}"
            assert item["titleSource"] in ("auto_generated", "fallback"), (
                f"Expected auto_generated/fallback, got {item.get('titleSource')}"
            )

    def test_no_title_items_preserve_description(self):
        """Description must remain the full original text, not trimmed for the title."""
        result = generate_information_structure(
            self.NO_TITLE_REPORT,
            compression_mode="strict",
            target_point_count="all",
            input_profile="report_overview_items",
        )
        descriptions = [item["description"] for item in result["items"]]
        assert any("成本和调用稳定性" in d for d in descriptions), (
            f"Description truncated: {descriptions}"
        )
        assert any("代码修改和测试" in d for d in descriptions), (
            f"Description truncated: {descriptions}"
        )

    def test_no_title_items_attach_evidence(self):
        """Evidence lines should still attach to their preceding items."""
        result = generate_information_structure(
            self.NO_TITLE_REPORT,
            compression_mode="strict",
            target_point_count="all",
            input_profile="report_overview_items",
        )
        assert len(result["items"]) == 2
        # At least one item should have evidence
        items_with_evidence = [item for item in result["items"] if item.get("evidence")]
        assert len(items_with_evidence) >= 1, (
            f"No evidence attached: {[item.get('evidence') for item in result['items']]}"
        )

    def test_mixed_report_first_item_explicit_second_auto(self):
        """First item has explicit title, second has auto-generated."""
        result = generate_information_structure(
            self.MIXED_REPORT,
            compression_mode="strict",
            target_point_count="all",
            input_profile="report_overview_items",
        )
        assert len(result["items"]) == 2
        assert result["items"][0]["titleSource"] == "explicit", (
            f"Expected explicit for item 1, got {result['items'][0]['titleSource']}"
        )
        assert result["items"][1]["titleSource"] in ("auto_generated", "fallback"), (
            f"Expected auto_generated for item 2, got {result['items'][1]['titleSource']}"
        )

    def test_single_paragraph_no_title_produces_item(self):
        """A single no-title paragraph should produce at least 1 item."""
        result = generate_information_structure(
            self.SINGLE_PARAGRAPH_NO_TITLE,
            compression_mode="strict",
            target_point_count="all",
            input_profile="report_overview_items",
        )
        # Either overview + 1 item, or 1 item directly
        total = result["stats"]["detectedItemCount"]
        assert total >= 1, f"Single paragraph produced 0 items: {result}"
        # The item should have a title
        assert any(item.get("title") for item in result["items"]), (
            f"No item has a title: {result['items']}"
        )
        # The item should have a description
        assert any(item.get("description") for item in result["items"]), (
            f"No item has a description: {result['items']}"
        )


class TestDeriveItemTitle:
    """Tests for _derive_item_title_from_description."""

    def test_truncates_at_sentence_terminator(self):
        title, source = _derive_item_title_from_description(
            "OpenAI 发布新模型，推理能力提升，但成本仍需观察。", 1
        )
        assert source == "auto_generated"
        assert title == "OpenAI 发布新模型"

    def test_truncates_at_comma_for_long_first_sentence(self):
        long_desc = "这一变化说明开发者工具正在从代码补全走向任务代理，AI 编程正进入新阶段。"
        title, source = _derive_item_title_from_description(long_desc, 1)
        assert source == "auto_generated"
        # Should cut at the first comma since the sentence is long
        assert len(title) <= 24, f"Title too long: {title}"

    def test_empty_description_returns_fallback(self):
        title, source = _derive_item_title_from_description("", 3)
        assert title == "信息点 3"
        assert source == "fallback"

    def test_strips_trailing_punctuation(self):
        title, source = _derive_item_title_from_description(
            "Claude Code 新增能力，开发者可以更方便地完成代码修改和测试。", 1
        )
        assert not title.endswith(("。", "！", "?", "."))
        assert source == "auto_generated"


class TestNoTitleBlockSplitting:
    """Tests for _split_report_item_blocks with no-title paragraphs."""

    def test_no_title_paragraphs_are_separate_blocks(self):
        content = (
            "今日 AI 前沿\n\n"
            "OpenAI 发布新模型，推理能力提升。\n\n"
            "Claude Code 新增能力，开发者体验改善。"
        )
        blocks = _split_report_item_blocks(content)
        # Should have 3 blocks: overview + 2 no-title items
        assert len(blocks) == 3, f"Got {len(blocks)} blocks: {blocks}"

    def test_explicit_items_still_split_correctly(self):
        content = (
            "今日 AI 前沿\n\n"
            "模型发布：OpenAI 发布新模型，推理能力提升。\n\n"
            "开发工具：Claude Code 新增能力，开发者体验改善。"
        )
        blocks = _split_report_item_blocks(content)
        assert len(blocks) == 3, f"Got {len(blocks)} blocks: {blocks}"


class TestSerializeNoTitleItems:
    """Tests for serialize_for_visual_compose with auto-generated titles."""

    def test_serialize_includes_title_for_no_title_items(self):
        result = generate_information_structure(
            "今日 AI 前沿\n\n"
            "OpenAI 发布新模型，推理能力提升，但成本仍需观察。\n\n"
            "Claude Code 新增能力，开发者体验改善。",
            compression_mode="strict",
            target_point_count="all",
            input_profile="report_overview_items",
        )
        serialized = serialize_for_visual_compose(result)
        # Should contain 【信息点 1】 and 【信息点 2】 with 标题： lines
        assert "【信息点 1】" in serialized
        assert "【信息点 2】" in serialized
        # Each item should have both 标题 and 描述
        assert serialized.count("【信息点") == 2, serialized
        # Each item section should have a 标题 line
        assert serialized.count("标题：") >= 2, (
            f"Expected ≥2 标题： lines, got: {serialized}"
        )
        # Verify every 标题： is followed by a 描述： for items (not just overview)
        item_blocks = serialized.split("【信息点")
        for i, block in enumerate(item_blocks[1:], 1):
            assert "标题：" in block, f"信息点 {i} missing 标题"
            assert "描述：" in block, f"信息点 {i} missing 描述"
