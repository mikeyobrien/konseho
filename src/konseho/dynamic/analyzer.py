"""Query analyzer to understand task requirements and suggest council configuration."""
from __future__ import annotations

import re
from enum import Enum
from typing import Any


class TaskType(Enum):
    __slots__ = ()
    """Types of tasks that require different council configurations."""
    RESEARCH = 'research'
    CODE_REVIEW = 'code_review'
    DESIGN = 'design'
    ANALYSIS = 'analysis'
    PLANNING = 'planning'
    DEBATE = 'debate'
    IMPLEMENTATION = 'implementation'
    GENERAL = 'general'


class QueryAnalyzer:
    __slots__ = ()
    """Analyzes user queries to determine optimal council configuration."""

    def __init__(self):
        self.task_patterns = {TaskType.RESEARCH: ['\\bresearch\\b',
            '\\bfind out\\b', '\\bexplore\\b', '\\binvestigate\\b',
            '\\bgather information\\b', '\\blearn about\\b', '\\bstudy\\b'],
            TaskType.CODE_REVIEW: ['\\breview\\b.*\\bcode\\b',
            '\\bcode review\\b', '\\bcheck.*\\bcode\\b', '\\baudit\\b',
            '\\bfind.*\\bbug\\b', '\\banalyze.*\\bcode\\b'], TaskType.
            DESIGN: ['\\bdesign\\b', '\\barchitect\\b',
            '\\bcreate.*\\bsystem\\b', '\\bpropose.*\\bsolution\\b',
            '\\bbuild\\b', '\\bimplement\\b'], TaskType.ANALYSIS: [
            '\\banalyze\\b', '\\bevaluate\\b', '\\bassess\\b',
            '\\bcompare\\b', '\\bexamine\\b', '\\binspect\\b',
            '\\bstudy\\b'], TaskType.PLANNING: ['\\bplan\\b',
            '\\bstrategy\\b', '\\broadmap\\b', '\\borganize\\b',
            '\\bschedule\\b', '\\bcoordinate\\b'], TaskType.DEBATE: [
            '\\bdebate\\b', '\\bdiscuss\\b', '\\bpros.*\\bcons\\b',
            '\\bargue\\b', '\\bcontrast\\b', '\\bcompare.*\\bapproaches\\b'
            ], TaskType.IMPLEMENTATION: ['\\bimplement\\b', '\\bcode\\b',
            '\\bbuild\\b', '\\bcreate\\b', '\\bdevelop\\b',
            '\\bwrite.*\\bcode\\b']}
        self.domain_keywords = {'technical': ['code', 'api', 'database',
            'system', 'architecture', 'algorithm'], 'business': ['strategy',
            'market', 'customer', 'revenue', 'growth'], 'creative': [
            'design', 'user', 'experience', 'interface', 'creative'],
            'scientific': ['research', 'data', 'analysis', 'hypothesis',
            'experiment']}

    def analyze(self, query: str) ->dict[str, Any]:
        """Analyze a query and return configuration suggestions."""
        query_lower = query.lower()
        task_type = self._detect_task_type(query_lower)
        domains = self._detect_domains(query_lower)
        complexity = self._estimate_complexity(query)
        agent_count = self._suggest_agent_count(task_type, complexity, domains)
        needs_parallel = self._needs_parallel_work(task_type, domains)
        needs_debate = self._needs_debate(task_type, query_lower)
        return {'task_type': task_type, 'domains': domains, 'complexity':
            complexity, 'suggested_agent_count': agent_count,
            'needs_parallel': needs_parallel, 'needs_debate': needs_debate,
            'query': query}

    def _detect_task_type(self, query: str) ->TaskType:
        """Detect the primary task type from the query."""
        for task_type, patterns in self.task_patterns.items():
            for pattern in patterns:
                if re.search(pattern, query):
                    return task_type
        return TaskType.GENERAL

    def _detect_domains(self, query: str) ->list[str]:
        """Detect domains mentioned in the query."""
        detected = []
        for domain, keywords in self.domain_keywords.items():
            if any(keyword in query for keyword in keywords):
                detected.append(domain)
        return detected if detected else ['general']

    def _estimate_complexity(self, query: str) ->str:
        """Estimate task complexity based on query characteristics."""
        word_count = len(query.split())
        has_multiple_parts = any(word in query.lower() for word in ['and',
            'also', 'then', 'multiple', 'various'])
        has_constraints = any(word in query.lower() for word in ['must',
            'should', 'require', 'constraint', 'ensure'])
        if word_count > 50 or has_multiple_parts and has_constraints:
            return 'high'
        elif word_count > 20 or has_multiple_parts or has_constraints:
            return 'medium'
        else:
            return 'low'

    def _suggest_agent_count(self, task_type: TaskType, complexity: str,
        domains: list[str]) ->int:
        """Suggest optimal number of agents."""
        base_count = {TaskType.RESEARCH: 3, TaskType.CODE_REVIEW: 4,
            TaskType.DESIGN: 3, TaskType.ANALYSIS: 3, TaskType.PLANNING: 3,
            TaskType.DEBATE: 2, TaskType.IMPLEMENTATION: 2, TaskType.GENERAL: 3
            }
        count = base_count.get(task_type, 3)
        if complexity == 'high':
            count += 1
        if len(domains) > 2:
            count += 1
        return min(count, 6)

    def _needs_parallel_work(self, task_type: TaskType, domains: list[str]
        ) ->bool:
        """Determine if parallel execution would be beneficial."""
        if task_type in [TaskType.RESEARCH, TaskType.ANALYSIS] and len(domains
            ) > 1:
            return True
        if task_type == TaskType.IMPLEMENTATION:
            return True
        return False

    def _needs_debate(self, task_type: TaskType, query: str) ->bool:
        """Determine if debate/discussion would be beneficial."""
        if task_type in [TaskType.DEBATE, TaskType.DESIGN, TaskType.PLANNING]:
            return True
        debate_keywords = ['best', 'optimal', 'compare', 'choose', 'decide',
            'option']
        return any(keyword in query for keyword in debate_keywords)
