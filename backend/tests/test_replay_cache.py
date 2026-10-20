"""replay_cache 模块单元测试。

覆盖目标（对应软件测试课覆盖准则）：
- 语句覆盖：每个函数至少一条用例走到。
- 分支覆盖：每个 if 的 True / False 两边都要有用例。
- 条件覆盖：save_turn 中「空查询早返回」与「来源列表为空/非空」两条路径。
Mock 用法：用 unittest.mock.patch 隔离文件 I/O（_load/_save）与配置变量（LLM_API_KEY），
避免测试真正读写磁盘或依赖 .env 环境。
"""
import pytest
from unittest.mock import patch

from app.agents import replay_cache as rc


# ---------------- _normalize ----------------
def test_normalize_empty_returns_empty():
    # 分支：if not text -> True
    assert rc._normalize("") == ""


def test_normalize_strips_punct_and_space():
    # 分支：if not text -> False，走 _PUNCT.sub
    assert rc._normalize("  你好，世界！ ") == "你好世界"


def test_normalize_only_punct_becomes_empty():
    # 走 sub 分支（非早返回），但结果恰为空串
    assert rc._normalize("！！！？？？") == ""


# ---------------- is_offline（mock 模块全局变量） ----------------
def test_is_offline_true_when_no_key():
    with patch.object(rc, "LLM_API_KEY", ""):
        assert rc.is_offline() is True


def test_is_offline_false_when_key_set():
    with patch.object(rc, "LLM_API_KEY", "sk-abc123"):
        assert rc.is_offline() is False


# ---------------- lookup（mock _load） ----------------
def test_lookup_empty_query_returns_none():
    # 归一化后为空，直接返回 None，不经过 _load
    assert rc.lookup("") is None
    assert rc.lookup("  ！！  ") is None


def test_lookup_hit():
    cached = {"你好世界": {"query": "你好，世界！", "answer": "hi", "sources": []}}
    with patch.object(rc, "_load", return_value=cached):
        hit = rc.lookup("你好，世界！")
    assert hit == cached["你好世界"]


def test_lookup_miss_returns_none():
    with patch.object(rc, "_load", return_value={}):
        assert rc.lookup("一个不存在的问题") is None


# ---------------- save_turn（mock _load + _save） ----------------
def test_save_turn_skips_empty_query():
    with patch.object(rc, "_load", return_value={}) as mload, \
         patch.object(rc, "_save") as msave:
        rc.save_turn("   ", "答案", [])
    msave.assert_not_called()  # 空查询早返回，不写盘


def test_save_turn_writes_normalized_key():
    captured = {}
    with patch.object(rc, "_load", return_value={}), \
         patch.object(rc, "_save", side_effect=lambda d: captured.update(d)):
        rc.save_turn("门票多少钱？", "100元", None)
    assert "门票多少钱" in captured
    assert captured["门票多少钱"]["answer"] == "100元"
    assert captured["门票多少钱"]["sources"] == []


def test_save_turn_truncates_source_text():
    captured = {}
    sources = [{"source": "s1", "category": "c1", "text": "x" * 500}]
    with patch.object(rc, "_load", return_value={}), \
         patch.object(rc, "_save", side_effect=lambda d: captured.update(d)):
        rc.save_turn("问个问题", "答", sources)
    saved_src = captured["问个问题"]["sources"][0]
    assert saved_src["source"] == "s1"
    assert len(saved_src["text"]) == 400  # 来源文本截断到 400 字


# ---------------- count（mock _load） ----------------
def test_count_returns_number_of_entries():
    with patch.object(rc, "_load", return_value={"a": 1, "b": 2, "c": 3}):
        assert rc.count() == 3


# ---------------- 真实文件读写（不 mock，用 tmp_path 夹具） ----------------
def test_save_then_load_roundtrip(tmp_path):
    """对比上组用例：这里不 mock，改用临时文件验证 _save/_load 真实主路径。"""
    cache_file = tmp_path / "replay_cache.json"
    with patch.object(rc, "CACHE_FILE", cache_file):
        rc.save_turn("开放时间？", "8:00-18:00", [{"source": "s", "category": "c", "text": "详情"}])
        hit = rc.lookup("开放时间？")
        assert rc.count() == 1
    assert hit is not None
    assert hit["answer"] == "8:00-18:00"


# ---------------- 故障注入：覆盖异常分支（冲 100% 覆盖率） ----------------
def test_load_handles_corrupted_json(tmp_path):
    """故障注入：缓存文件存在但内容非法，json.load 抛异常应被吞掉返回 {}。"""
    bad_file = tmp_path / "bad.json"
    bad_file.write_text("{这不是合法json", encoding="utf-8")
    with patch.object(rc, "CACHE_FILE", bad_file):
        assert rc._load() == {}   # 命中 except 分支（行 35-36）


def test_save_handles_write_error():
    """故障注入：写入时 open 抛异常，验证异常被捕获并记录告警（行 43-44）。"""
    with patch.object(rc, "open", side_effect=OSError("磁盘已满")), \
         patch.object(rc.logger, "warning") as mock_warn:
        rc._save({"k": "v"})      # 不应向上抛异常
    mock_warn.assert_called_once()
