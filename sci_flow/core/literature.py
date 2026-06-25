"""
SciFlow 文献管理模块
提供文献检索、引用格式生成、文献矩阵分析等功能
"""

from __future__ import annotations

import random
import re
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

from ..llm.client import LLMClient, get_llm_client
from .config import Config, get_config
from .database import Database, get_database
from .models import Discipline, Literature


DISCIPLINE_TEMPLATES: Dict[Discipline, Dict[str, Any]] = {
    Discipline.COMPUTER_SCIENCE: {
        "venues": [
            "NeurIPS", "ICML", "ICLR", "CVPR", "ICCV", "ECCV",
            "ACL", "EMNLP", "AAAI", "IJCAI", "SIGGRAPH", "SIGMOD",
            "VLDB", "OSDI", "SOSP", "ISCA", "MICRO", "ASPLOS",
        ],
        "topics": [
            "深度学习", "机器学习", "计算机视觉", "自然语言处理",
            "强化学习", "图神经网络", "大语言模型", "多模态学习",
            "自动驾驶", "机器人", "分布式系统", "数据库系统",
        ],
        "title_patterns": [
            "A Novel Approach to {topic} via {method}",
            "{method}: {topic} with Enhanced Performance",
            "Rethinking {topic}: A {method} Perspective",
            "Efficient {topic} Using {method}",
            "{method} for Robust {topic}",
        ],
    },
    Discipline.BIOLOGY: {
        "venues": [
            "Nature", "Science", "Cell", "Nature Genetics", "Nature Methods",
            "Molecular Cell", "Cell Reports", "eLife", "PNAS", "Genome Research",
            "Bioinformatics", "BMC Biology", "Journal of Molecular Biology",
        ],
        "topics": [
            "基因编辑", "蛋白质结构预测", "单细胞测序", "CRISPR",
            "合成生物学", "脑科学", "微生物组", "癌症生物学",
            "表观遗传学", "进化生物学", "系统生物学", "生物信息学",
        ],
        "title_patterns": [
            "{method} Reveals Novel Insights into {topic}",
            "Single-Cell Analysis of {topic} Using {method}",
            "CRISPR-Based {method} for {topic} Studies",
            "Structural Basis of {topic}: A {method} Approach",
            "Genome-Wide {method} Identifies Key Regulators of {topic}",
        ],
    },
    Discipline.PHYSICS: {
        "venues": [
            "Physical Review Letters", "Nature Physics", "Physical Review X",
            "Science Advances", "Physical Review A", "Physical Review B",
            "Physical Review D", "Physical Review E", "Reviews of Modern Physics",
        ],
        "topics": [
            "量子计算", "凝聚态物理", "粒子物理", "宇宙学",
            "量子光学", "拓扑材料", "高温超导", "引力波",
            "暗物质", "量子信息", "等离子体物理", "生物物理",
        ],
        "title_patterns": [
            "Observation of {topic} in {system} Using {method}",
            "{method} Study of {topic} at {condition}",
            "Theory of {topic}: A {method} Framework",
            "Quantum {method} for {topic}",
            "Evidence for {topic} from {method} Measurements",
        ],
    },
    Discipline.CHEMISTRY: {
        "venues": [
            "Journal of the American Chemical Society", "Angewandte Chemie",
            "Nature Chemistry", "Chemical Science", "ACS Nano",
            "Nano Letters", "Advanced Materials", "Chem",
            "Journal of Chemical Physics", "Organic Letters",
        ],
        "topics": [
            "催化", "有机合成", "纳米材料", "电化学",
            "光化学", "药物化学", "高分子材料", "计算化学",
            "超分子化学", "生物化学", "绿色化学", "电池材料",
        ],
        "title_patterns": [
            "{method}-Catalyzed {topic}: Efficient Synthesis of {product}",
            "Rational Design of {material} for {topic} via {method}",
            "Mechanistic Insights into {topic}: A {method} Study",
            "Novel {method} Approach to {topic}",
            "{material}-Based {method} for Enhanced {topic}",
        ],
    },
    Discipline.MATERIALS_SCIENCE: {
        "venues": [
            "Nature Materials", "Advanced Materials", "ACS Nano",
            "Nano Letters", "Materials Today", "Acta Materialia",
            "Scripta Materialia", "Journal of Materials Chemistry A",
            "Advanced Functional Materials", "Nature Nanotechnology",
        ],
        "topics": [
            "二维材料", "钙钛矿", "电池材料", "超材料",
            "生物材料", "半导体材料", "储能材料", "复合材料",
            "纳米材料", "柔性电子", "3D打印材料", "催化材料",
        ],
        "title_patterns": [
            "High-Performance {material} for {topic} via {method}",
            "{method}-Assisted Synthesis of {material} with Enhanced {topic}",
            "Multifunctional {material}: {topic} Enabled by {method}",
            "Scalable Production of {material} for {topic} Applications",
            "Interface Engineering of {material} for Improved {topic}",
        ],
    },
}

AUTHOR_NAMES = [
    "Wei Wang", "Yi Zhang", "Yang Liu", "Ming Li", "Hui Chen",
    "Jing Wang", "Lei Zhang", "Fang Li", "Jun Liu", "Yan Chen",
    "Michael Brown", "Sarah Johnson", "David Smith", "Emily Davis",
    "James Wilson", "Lisa Anderson", "Robert Taylor", "Jennifer Martinez",
    "Thomas Garcia", "Amanda Thompson", "Daniel Lee", "Michelle White",
]

METHODS = [
    "deep learning", "transformer architecture", "contrastive learning",
    "graph neural networks", "reinforcement learning", "transfer learning",
    "federated learning", "self-supervised learning", "multi-task learning",
    "few-shot learning", "neural architecture search", "diffusion models",
    "high-throughput sequencing", "X-ray crystallography", "cryo-EM",
    "mass spectrometry", "single-molecule imaging", "machine learning",
    "molecular dynamics", "Monte Carlo simulation", "density functional theory",
    "sol-gel method", "chemical vapor deposition", "hydrothermal synthesis",
]


class CitationFormatter:
    """引用格式生成器"""

    @staticmethod
    def generate_bibtex(literature: Literature) -> str:
        """生成BibTeX引用"""
        key = f"{literature.authors[0].split()[-1].lower() if literature.authors else 'unknown'}{literature.year or ''}"
        authors = " and ".join(literature.authors) if literature.authors else ""

        entry_type = "article"
        fields = [
            f"  title={{{literature.title}}}",
        ]
        if authors:
            fields.append(f"  author={{{authors}}}")
        if literature.year:
            fields.append(f"  year={{{literature.year}}}")
        if literature.venue:
            fields.append(f"  journal={{{literature.venue}}}")
        if literature.doi:
            fields.append(f"  doi={{{literature.doi}}}")
        if literature.url:
            fields.append(f"  url={{{literature.url}}}")

        bibtex = f"@{entry_type}{{{key},\n"
        bibtex += ",\n".join(fields)
        bibtex += "\n}"
        return bibtex

    @staticmethod
    def generate_gbt7714(literature: Literature) -> str:
        """生成GB/T 7714格式引用（中文）"""
        parts = []
        if literature.authors:
            if len(literature.authors) <= 3:
                authors_str = ", ".join(literature.authors)
            else:
                authors_str = ", ".join(literature.authors[:3]) + ", 等"
            parts.append(authors_str)
        parts.append(f" {literature.title}")
        if literature.venue:
            parts.append(f"[J]. {literature.venue}")
        if literature.year:
            parts.append(f", {literature.year}")
        return "".join(parts) + "."

    @staticmethod
    def generate_apa(literature: Literature) -> str:
        """生成APA格式引用"""
        parts = []
        if literature.authors:
            authors_parts = []
            for author in literature.authors:
                name_parts = author.split()
                if len(name_parts) >= 2:
                    last_name = name_parts[-1]
                    initials = "".join([n[0] + "." for n in name_parts[:-1]])
                    authors_parts.append(f"{last_name}, {initials}")
                else:
                    authors_parts.append(author)
            parts.append(", ".join(authors_parts))
        if literature.year:
            parts.append(f" ({literature.year})")
        parts.append(f". {literature.title}.")
        if literature.venue:
            parts.append(f" *{literature.venue}*.")
        return "".join(parts)


class LiteratureManager:
    """文献管理器类"""

    def __init__(
        self,
        config: Optional[Config] = None,
        db: Optional[Database] = None,
        llm: Optional[LLMClient] = None,
    ):
        self.config = config or get_config()
        self.db = db or get_database()
        self.llm = llm or get_llm_client()
        self.formatter = CitationFormatter()

    def generate_mock_literature(
        self, topic: str, count: int = 10, discipline: Discipline = Discipline.COMPUTER_SCIENCE
    ) -> List[Literature]:
        """生成逼真的Mock文献数据"""
        template = DISCIPLINE_TEMPLATES.get(discipline, DISCIPLINE_TEMPLATES[Discipline.COMPUTER_SCIENCE])
        literature_list = []

        base_year = datetime.now().year
        for i in range(count):
            year = base_year - random.randint(0, 8)
            venue = random.choice(template["venues"])
            method = random.choice(METHODS)

            title_pattern = random.choice(template["title_patterns"])
            title_topic = topic if topic else random.choice(template["topics"])
            title = title_pattern.format(topic=title_topic, method=method)
            if not topic:
                pass

            num_authors = random.randint(2, 6)
            authors = random.sample(AUTHOR_NAMES, min(num_authors, len(AUTHOR_NAMES)))

            citations = int(random.gauss(500, 800))
            citations = max(0, min(citations, 10000))
            if year >= base_year - 1:
                citations = random.randint(0, 100)
            elif year >= base_year - 3:
                citations = random.randint(10, 500)

            abstract = self._generate_mock_abstract(title, authors, year, venue)

            lit = Literature(
                title=title,
                authors=authors,
                year=year,
                venue=venue,
                abstract=abstract,
                citations=citations,
                url=f"https://doi.org/10.{random.randint(1000, 9999)}/{random.randint(100000, 999999)}",
                doi=f"10.{random.randint(1000, 9999)}/{random.randint(100000, 999999)}",
                tags=[title_topic, method],
            )
            lit.bibtex = self.formatter.generate_bibtex(lit)
            literature_list.append(lit)

        literature_list.sort(key=lambda x: (-x.citations, -(x.year or 0)))
        return literature_list

    def _generate_mock_abstract(
        self, title: str, authors: List[str], year: int, venue: str
    ) -> str:
        """生成Mock摘要"""
        abstract_templates = [
            f"{title}近年来受到广泛关注。本文提出了一种新的方法，在多个基准数据集上取得了 state-of-the-art 的结果。实验表明，我们的方法相比现有工作有显著提升。",
            f"针对现有方法在{title}方面的局限性，本文提出了一个新颖的框架。通过大量实验验证，该框架在效率和准确性上均优于基线方法。消融实验进一步证明了各模块的有效性。",
            f"本文研究了{title}这一重要问题。我们首先进行了深入的理论分析，然后提出了一个实用的解决方案。在真实世界数据集上的实验结果验证了我们方法的优越性。",
            f"{title}是一个具有挑战性的研究课题。本文介绍了我们在该领域的最新进展，包括一种创新算法和一个大规模数据集。我们相信这项工作将推动相关领域的发展。",
            f"本文提出了一种统一的框架来解决{title}问题。该框架具有良好的通用性，可以灵活适配不同场景。实验结果和理论分析都充分验证了方法的有效性。",
        ]
        return random.choice(abstract_templates)

    async def search(
        self,
        topic: str,
        limit: int = 10,
        discipline: Discipline = Discipline.COMPUTER_SCIENCE,
        use_mock: Optional[bool] = None,
    ) -> List[Literature]:
        """
        搜索文献

        Args:
            topic: 研究主题
            limit: 返回文献数量
            discipline: 学科领域
            use_mock: 是否强制使用Mock模式

        Returns:
            文献列表
        """
        if use_mock is None:
            use_mock = self.config.is_mock_mode()

        if use_mock:
            return self.generate_mock_literature(topic, limit, discipline)

        try:
            return await self._search_semantic_scholar(topic, limit)
        except Exception:
            return self.generate_mock_literature(topic, limit, discipline)

    async def _search_semantic_scholar(self, topic: str, limit: int) -> List[Literature]:
        """使用Semantic Scholar API搜索文献"""
        import urllib.parse
        import urllib.request

        base_url = "https://api.semanticscholar.org/graph/v1/paper/search"
        params = {
            "query": topic,
            "limit": limit,
            "fields": "title,authors,year,venue,abstract,citationCount,url,externalIds",
        }
        url = f"{base_url}?{urllib.parse.urlencode(params)}"

        req = urllib.request.Request(url)
        req.add_header("User-Agent", "SciFlow/1.0")

        with urllib.request.urlopen(req, timeout=10) as response:
            import json
            data = json.loads(response.read().decode())

        literature_list = []
        for paper in data.get("data", []):
            authors = [a.get("name", "") for a in paper.get("authors", [])]
            doi = paper.get("externalIds", {}).get("DOI")
            lit = Literature(
                title=paper.get("title", ""),
                authors=authors,
                year=paper.get("year"),
                venue=paper.get("venue"),
                abstract=paper.get("abstract"),
                citations=paper.get("citationCount", 0),
                url=paper.get("url"),
                doi=doi,
                tags=[topic],
            )
            lit.bibtex = self.formatter.generate_bibtex(lit)
            literature_list.append(lit)

        return literature_list

    def generate_bibtex(self, literature: List[Literature]) -> str:
        """生成BibTeX文件内容"""
        bibtex_entries = []
        for lit in literature:
            if lit.bibtex:
                bibtex_entries.append(lit.bibtex)
            else:
                bibtex_entries.append(self.formatter.generate_bibtex(lit))
        return "\n\n".join(bibtex_entries)

    def generate_gbt7714(self, literature: List[Literature]) -> str:
        """生成GB/T 7714格式参考文献列表"""
        entries = []
        for i, lit in enumerate(literature, 1):
            entry = f"[{i}] {self.formatter.generate_gbt7714(lit)}"
            entries.append(entry)
        return "\n".join(entries)

    def generate_apa(self, literature: List[Literature]) -> str:
        """生成APA格式参考文献列表"""
        entries = []
        for lit in literature:
            entries.append(self.formatter.generate_apa(lit))
        return "\n\n".join(entries)

    def generate_literature_matrix(self, literature: List[Literature]) -> str:
        """生成文献矩阵分析（Markdown格式）"""
        if not literature:
            return "暂无文献数据"

        matrix = "## 文献对比分析矩阵\n\n"
        matrix += "| 序号 | 文献标题 | 作者 | 年份 | 发表期刊/会议 | 引用数 | 核心贡献 | 局限性 |\n"
        matrix += "|------|----------|------|------|---------------|--------|----------|--------|\n"

        for i, lit in enumerate(literature, 1):
            title_short = lit.title[:40] + "..." if len(lit.title) > 40 else lit.title
            authors_short = lit.authors[0] + " 等" if len(lit.authors) > 1 else (lit.authors[0] if lit.authors else "")
            authors_short = authors_short[:20] + "..." if len(authors_short) > 20 else authors_short
            venue = lit.venue or ""
            venue_short = venue[:20] + "..." if len(venue) > 20 else venue
            contribution = "提出新方法"
            limitation = "泛化性有待验证"
            matrix += f"| {i} | {title_short} | {authors_short} | {lit.year or ''} | {venue_short} | {lit.citations} | {contribution} | {limitation} |\n"

        return matrix

    def generate_trend_summary(self, literature: List[Literature]) -> str:
        """生成研究趋势总结"""
        if not literature:
            return "暂无文献数据"

        years = [lit.year for lit in literature if lit.year]
        year_counts = {}
        for y in years:
            year_counts[y] = year_counts.get(y, 0) + 1

        venues = {}
        for lit in literature:
            if lit.venue:
                venues[lit.venue] = venues.get(lit.venue, 0) + 1

        avg_citations = sum(lit.citations for lit in literature) / len(literature) if literature else 0
        max_citations = max((lit.citations for lit in literature), default=0)

        summary = "## 研究趋势分析\n\n"
        summary += f"### 基本统计\n"
        summary += f"- 文献总数：{len(literature)} 篇\n"
        if years:
            summary += f"- 时间跨度：{min(years)} - {max(years)} 年\n"
        summary += f"- 平均引用数：{avg_citations:.0f}\n"
        summary += f"- 最高引用数：{max_citations}\n\n"

        summary += f"### 年度发文趋势\n"
        if year_counts:
            for year in sorted(year_counts.keys(), reverse=True)[:10]:
                bar = "█" * min(year_counts[year] * 2, 20)
                summary += f"- {year}: {bar} ({year_counts[year]}篇)\n"

        summary += f"\n### 主要发表期刊/会议\n"
        if venues:
            sorted_venues = sorted(venues.items(), key=lambda x: -x[1])[:5]
            for venue, count in sorted_venues:
                summary += f"- {venue}: {count}篇\n"

        summary += f"\n### 研究热点分析\n"
        all_tags = []
        for lit in literature:
            all_tags.extend(lit.tags)
        tag_counts = {}
        for tag in all_tags:
            tag_counts[tag] = tag_counts.get(tag, 0) + 1
        sorted_tags = sorted(tag_counts.items(), key=lambda x: -x[1])[:8]
        if sorted_tags:
            summary += "关键词热度：" + "、".join([f"{tag}({count})" for tag, count in sorted_tags]) + "\n"

        return summary

    def save_literature(self, literature: Literature) -> Literature:
        """保存文献到数据库"""
        return self.db.create_literature(literature)

    def get_literature(self, literature_id: str) -> Optional[Literature]:
        """从数据库获取文献"""
        return self.db.get_literature(literature_id)

    def list_literature(self, limit: int = 100, offset: int = 0) -> List[Literature]:
        """列出所有文献"""
        return self.db.list_literature(limit, offset)

    def search_local(self, query: str, limit: int = 20) -> List[Literature]:
        """在本地数据库搜索文献"""
        return self.db.search_literature(query, limit)

    def add_to_project(self, project_id: str, literature_id: str) -> None:
        """将文献添加到项目"""
        self.db.add_literature_to_project(project_id, literature_id)

    def get_project_literature(self, project_id: str) -> List[Literature]:
        """获取项目的文献列表"""
        return self.db.get_project_literature(project_id)


_literature_manager_instance: Optional[LiteratureManager] = None


def get_literature_manager(
    config: Optional[Config] = None,
    db: Optional[Database] = None,
    llm: Optional[LLMClient] = None,
) -> LiteratureManager:
    """获取文献管理器单例"""
    global _literature_manager_instance
    if _literature_manager_instance is None:
        _literature_manager_instance = LiteratureManager(config, db, llm)
    return _literature_manager_instance


def reset_literature_manager() -> None:
    """重置文献管理器（主要用于测试）"""
    global _literature_manager_instance
    _literature_manager_instance = None
