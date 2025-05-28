"""Query analyzer to understand task requirements and suggest council configuration."""

import re
from enum import Enum
from typing import Any


class TaskType(Enum):
    """Types of tasks that require different council configurations."""

    RESEARCH = "research"  # Requires exploration and synthesis
    CODE_REVIEW = "code_review"  # Requires multiple perspectives on code
    DESIGN = "design"  # Requires creative solutions and iteration
    ANALYSIS = "analysis"  # Requires deep examination from multiple angles
    PLANNING = "planning"  # Requires strategic thinking and coordination
    DEBATE = "debate"  # Requires contrasting viewpoints
    IMPLEMENTATION = "implementation"  # Requires practical execution
    GENERAL = "general"  # Default for unclear tasks


class QueryAnalyzer:
    """Analyzes user queries to determine optimal council configuration."""

    def __init__(self):
        self.task_patterns = {
            TaskType.RESEARCH: [
                r"\bresearch\b",
                r"\bfind out\b",
                r"\bexplore\b",
                r"\binvestigate\b",
                r"\bgather information\b",
                r"\blearn about\b",
                r"\bstudy\b",
            ],
            TaskType.CODE_REVIEW: [
                r"\breview\b.*\bcode\b",
                r"\bcode review\b",
                r"\bcheck.*\bcode\b",
                r"\baudit\b",
                r"\bfind.*\bbug\b",
                r"\banalyze.*\bcode\b",
            ],
            TaskType.DESIGN: [
                r"\bdesign\b",
                r"\barchitect\b",
                r"\bcreate.*\bsystem\b",
                r"\bpropose.*\bsolution\b",
                r"\bbuild\b",
                r"\bimplement\b",
            ],
            TaskType.ANALYSIS: [
                r"\banalyze\b",
                r"\bevaluate\b",
                r"\bassess\b",
                r"\bcompare\b",
                r"\bexamine\b",
                r"\binspect\b",
                r"\bstudy\b",
            ],
            TaskType.PLANNING: [
                r"\bplan\b",
                r"\bstrategy\b",
                r"\broadmap\b",
                r"\borganize\b",
                r"\bschedule\b",
                r"\bcoordinate\b",
            ],
            TaskType.DEBATE: [
                r"\bdebate\b",
                r"\bdiscuss\b",
                r"\bpros.*\bcons\b",
                r"\bargue\b",
                r"\bcontrast\b",
                r"\bcompare.*\bapproaches\b",
            ],
            TaskType.IMPLEMENTATION: [
                r"\bimplement\b",
                r"\bcode\b",
                r"\bbuild\b",
                r"\bcreate\b",
                r"\bdevelop\b",
                r"\bwrite.*\bcode\b",
            ],
        }

        self.domain_keywords = {
            "technical": [
                "code",
                "api",
                "database",
                "system",
                "architecture",
                "algorithm",
            ],
            "business": ["strategy", "market", "customer", "revenue", "growth"],
            "creative": ["design", "user", "experience", "interface", "creative"],
            "scientific": ["research", "data", "analysis", "hypothesis", "experiment"],
        }

    def analyze(self, query: str) -> dict[str, Any]:
        """Analyze a query and return configuration suggestions."""
        query_lower = query.lower()

        # Determine task type
        task_type = self._detect_task_type(query_lower)

        # Determine domains involved
        domains = self._detect_domains(query_lower)

        # Estimate complexity
        complexity = self._estimate_complexity(query)

        # Suggest number of agents
        agent_count = self._suggest_agent_count(task_type, complexity, domains)

        # Determine if parallel work is beneficial
        needs_parallel = self._needs_parallel_work(task_type, domains)

        # Determine if debate is beneficial
        needs_debate = self._needs_debate(task_type, query_lower)

        return {
            "task_type": task_type,
            "domains": domains,
            "complexity": complexity,
            "suggested_agent_count": agent_count,
            "needs_parallel": needs_parallel,
            "needs_debate": needs_debate,
            "query": query,
        }

    def _detect_task_type(self, query: str) -> TaskType:
        """Detect the primary task type from the query."""
        for task_type, patterns in self.task_patterns.items():
            for pattern in patterns:
                if re.search(pattern, query):
                    return task_type
        return TaskType.GENERAL

    def _detect_domains(self, query: str) -> list[str]:
        """Detect domains mentioned in the query."""
        detected = []
        for domain, keywords in self.domain_keywords.items():
            if any(keyword in query for keyword in keywords):
                detected.append(domain)
        return detected if detected else ["general"]

    def _estimate_complexity(self, query: str) -> str:
        """Estimate task complexity based on query characteristics."""
        # Simple heuristics for complexity
        word_count = len(query.split())
        has_multiple_parts = any(
            word in query.lower()
            for word in ["and", "also", "then", "multiple", "various"]
        )
        has_constraints = any(
            word in query.lower()
            for word in ["must", "should", "require", "constraint", "ensure"]
        )

        if word_count > 50 or (has_multiple_parts and has_constraints):
            return "high"
        elif word_count > 20 or has_multiple_parts or has_constraints:
            return "medium"
        else:
            return "low"

    def _suggest_agent_count(
        self, task_type: TaskType, complexity: str, domains: list[str]
    ) -> int:
        """Suggest optimal number of agents."""
        base_count = {
            TaskType.RESEARCH: 3,
            TaskType.CODE_REVIEW: 4,
            TaskType.DESIGN: 3,
            TaskType.ANALYSIS: 3,
            TaskType.PLANNING: 3,
            TaskType.DEBATE: 2,
            TaskType.IMPLEMENTATION: 2,
            TaskType.GENERAL: 3,
        }

        count = base_count.get(task_type, 3)

        # Adjust for complexity
        if complexity == "high":
            count += 1

        # Adjust for multiple domains
        if len(domains) > 2:
            count += 1

        return min(count, 6)  # Cap at 6 agents

    def _needs_parallel_work(self, task_type: TaskType, domains: list[str]) -> bool:
        """Determine if parallel execution would be beneficial."""
        # Parallel work is good for research, analysis with multiple domains
        if task_type in [TaskType.RESEARCH, TaskType.ANALYSIS] and len(domains) > 1:
            return True
        # Implementation benefits from parallel work on different components
        if task_type == TaskType.IMPLEMENTATION:
            return True
        return False

    def _needs_debate(self, task_type: TaskType, query: str) -> bool:
        """Determine if debate/discussion would be beneficial."""
        # Certain task types naturally benefit from debate
        if task_type in [TaskType.DEBATE, TaskType.DESIGN, TaskType.PLANNING]:
            return True
        # Look for keywords suggesting multiple perspectives are valuable
        debate_keywords = ["best", "optimal", "compare", "choose", "decide", "option"]
        return any(keyword in query for keyword in debate_keywords)
