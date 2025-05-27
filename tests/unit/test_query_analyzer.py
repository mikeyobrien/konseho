"""Unit tests for QueryAnalyzer."""

from konseho.dynamic.analyzer import QueryAnalyzer, TaskType


class TestQueryAnalyzer:
    """Test suite for QueryAnalyzer."""
    
    def setup_method(self):
        """Set up test dependencies."""
        self.analyzer = QueryAnalyzer()
    
    def test_detect_research_task(self):
        """Test detection of research tasks."""
        queries = [
            "research the latest trends in AI",
            "find out about quantum computing",
            "explore different database architectures",
            "investigate security vulnerabilities in web apps",
            "gather information about market trends"
        ]
        
        for query in queries:
            result = self.analyzer.analyze(query)
            assert result["task_type"] == TaskType.RESEARCH
    
    def test_detect_code_review_task(self):
        """Test detection of code review tasks."""
        queries = [
            "review this code for security issues",
            "code review for the authentication module",
            "check this code for bugs",
            "audit the payment processing code",
            "analyze this code for performance"
        ]
        
        for query in queries:
            result = self.analyzer.analyze(query)
            assert result["task_type"] == TaskType.CODE_REVIEW
    
    def test_detect_design_task(self):
        """Test detection of design tasks."""
        queries = [
            "design a scalable microservices architecture",
            "architect a solution for real-time data processing",
            "create a system for user authentication",
            "propose a solution for distributed caching",
            "implement a recommendation engine"
        ]
        
        for query in queries:
            result = self.analyzer.analyze(query)
            assert result["task_type"] == TaskType.DESIGN
    
    def test_detect_analysis_task(self):
        """Test detection of analysis tasks."""
        queries = [
            "analyze the performance metrics",
            "evaluate different cloud providers",
            "assess the security risks",
            "compare React vs Vue for our project",
            "examine the user behavior data"
        ]
        
        for query in queries:
            result = self.analyzer.analyze(query)
            assert result["task_type"] == TaskType.ANALYSIS
    
    def test_detect_planning_task(self):
        """Test detection of planning tasks."""
        queries = [
            "plan the migration to cloud",
            "create a strategy for scaling",
            "develop a roadmap for Q1",
            "organize the sprint schedule",
            "coordinate the deployment process"
        ]
        
        for query in queries:
            result = self.analyzer.analyze(query)
            assert result["task_type"] == TaskType.PLANNING
    
    def test_detect_debate_task(self):
        """Test detection of debate tasks."""
        queries = [
            "debate the pros and cons of microservices",
            "discuss whether to use SQL or NoSQL",
            "argue for and against serverless",
            "contrast different frontend frameworks",
            "compare different approaches to caching"
        ]
        
        for query in queries:
            result = self.analyzer.analyze(query)
            assert result["task_type"] == TaskType.DEBATE
    
    def test_detect_implementation_task(self):
        """Test detection of implementation tasks."""
        queries = [
            "implement user authentication",
            "code a REST API for products",
            "build a dashboard component",
            "create a data pipeline",
            "write code for the payment system"
        ]
        
        for query in queries:
            result = self.analyzer.analyze(query)
            assert result["task_type"] == TaskType.IMPLEMENTATION
    
    def test_detect_general_task(self):
        """Test fallback to general task type."""
        queries = [
            "help me with this",
            "what should I do",
            "I need assistance",
            "can you help"
        ]
        
        for query in queries:
            result = self.analyzer.analyze(query)
            assert result["task_type"] == TaskType.GENERAL
    
    def test_detect_domains(self):
        """Test domain detection."""
        test_cases = [
            ("build a REST API with database", ["technical"]),
            ("analyze market strategy for growth", ["business"]),
            ("design user interface with good experience", ["creative"]),
            ("research data analysis hypothesis", ["scientific"]),
            ("help me with something", ["general"])
        ]
        
        for query, expected_domains in test_cases:
            result = self.analyzer.analyze(query)
            assert result["domains"] == expected_domains
    
    def test_detect_multiple_domains(self):
        """Test detection of multiple domains."""
        query = "design a user-friendly API for customer data analysis"
        result = self.analyzer.analyze(query)
        assert "technical" in result["domains"]
        assert "creative" in result["domains"]
        assert len(result["domains"]) >= 2
    
    def test_complexity_estimation(self):
        """Test complexity estimation."""
        test_cases = [
            ("fix bug", "low"),
            ("implement authentication system with OAuth", "medium"),
            ("design and implement a distributed system with multiple microservices and ensure high availability", "high")
        ]
        
        for query, expected_complexity in test_cases:
            result = self.analyzer.analyze(query)
            assert result["complexity"] == expected_complexity
    
    def test_agent_count_suggestion(self):
        """Test agent count suggestions."""
        # Simple task
        result = self.analyzer.analyze("fix a bug")
        assert result["suggested_agent_count"] >= 2
        assert result["suggested_agent_count"] <= 3
        
        # Complex task with multiple domains
        result = self.analyzer.analyze(
            "design and implement a scalable API with database integration and user interface"
        )
        assert result["suggested_agent_count"] >= 4
        assert result["suggested_agent_count"] <= 6
    
    def test_parallel_work_detection(self):
        """Test detection of need for parallel work."""
        # Research with multiple domains should need parallel
        result = self.analyzer.analyze("research technical and business aspects of cloud migration")
        assert result["needs_parallel"] is True
        
        # Implementation always benefits from parallel
        result = self.analyzer.analyze("implement user authentication")
        assert result["needs_parallel"] is True
        
        # Simple debate doesn't need parallel
        result = self.analyzer.analyze("debate SQL vs NoSQL")
        assert result["needs_parallel"] is False
    
    def test_debate_need_detection(self):
        """Test detection of need for debate."""
        # Explicit debate tasks
        result = self.analyzer.analyze("debate the best approach")
        assert result["needs_debate"] is True
        
        # Design tasks benefit from debate
        result = self.analyzer.analyze("design a system architecture")
        assert result["needs_debate"] is True
        
        # Tasks with decision keywords
        result = self.analyzer.analyze("choose the best database option")
        assert result["needs_debate"] is True
        
        # Simple implementation doesn't need debate
        result = self.analyzer.analyze("implement the login function")
        assert result["needs_debate"] is False
    
    def test_complete_analysis_output(self):
        """Test that analysis returns all expected fields."""
        query = "research and analyze different approaches to build a scalable API"
        result = self.analyzer.analyze(query)
        
        # Check all expected fields are present
        assert "task_type" in result
        assert "domains" in result
        assert "complexity" in result
        assert "suggested_agent_count" in result
        assert "needs_parallel" in result
        assert "needs_debate" in result
        assert "query" in result
        
        # Check types
        assert isinstance(result["task_type"], TaskType)
        assert isinstance(result["domains"], list)
        assert isinstance(result["complexity"], str)
        assert isinstance(result["suggested_agent_count"], int)
        assert isinstance(result["needs_parallel"], bool)
        assert isinstance(result["needs_debate"], bool)
        assert result["query"] == query