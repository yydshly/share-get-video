from app.video_lab.services.information_structure_service import generate_information_structure


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
