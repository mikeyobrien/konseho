"""Integration tests for common workflow patterns."""


import pytest

from konseho import (
    AgentWrapper,
    Council,
    DebateStep,
    HumanAgent,
    ParallelStep,
    SplitStep,
)
from tests.fixtures import MockStrandsAgent


class TestCommonWorkflows:
    """Test common multi-agent workflow patterns."""
    
    @pytest.mark.asyncio
    async def test_research_synthesis_workflow(self):
        """Test research → synthesis → review workflow."""
        # Research phase - parallel researchers
        researcher1 = AgentWrapper(
            MockStrandsAgent("researcher1", "Found data about X"),
            name="researcher1"
        )
        researcher2 = AgentWrapper(
            MockStrandsAgent("researcher2", "Found data about Y"),
            name="researcher2"
        )
        
        # Synthesis phase - single synthesizer
        synthesizer = AgentWrapper(
            MockStrandsAgent("synthesizer", "Combined insights from X and Y"),
            name="synthesizer"
        )
        
        # Review phase - reviewers debate
        reviewer1 = AgentWrapper(
            MockStrandsAgent("reviewer1", "Good synthesis, approve"),
            name="reviewer1"
        )
        reviewer2 = AgentWrapper(
            MockStrandsAgent("reviewer2", "Needs improvement"),
            name="reviewer2"
        )
        
        council = Council(
            name="research_workflow",
            steps=[
                ParallelStep([researcher1, researcher2]),
                ParallelStep([synthesizer]),
                DebateStep([reviewer1, reviewer2], rounds=1)
            ]
        )
        
        result = await council.execute("Research topic Z")
        
        # Verify all phases executed
        assert "step_0" in result["results"]  # Research
        assert "step_1" in result["results"]  # Synthesis
        assert "step_2" in result["results"]  # Review
        
        # Verify data flow
        research_results = result["results"]["step_0"]["parallel_results"]
        assert "Found data about X" in research_results["researcher1"]
        assert "Found data about Y" in research_results["researcher2"]
    
    @pytest.mark.asyncio
    async def test_code_review_workflow(self):
        """Test code analysis → review → fix workflow."""
        # Analyze code in parallel
        security_analyzer = AgentWrapper(
            MockStrandsAgent("security", "No vulnerabilities found")
        )
        performance_analyzer = AgentWrapper(
            MockStrandsAgent("performance", "Could optimize loop at line 42")
        )
        style_analyzer = AgentWrapper(
            MockStrandsAgent("style", "Missing docstrings")
        )
        
        # Code fixer based on analysis
        fixer = AgentWrapper(
            MockStrandsAgent("fixer", "Fixed: optimized loop, added docstrings")
        )
        
        council = Council(
            name="code_review",
            steps=[
                ParallelStep([security_analyzer, performance_analyzer, style_analyzer]),
                ParallelStep([fixer])
            ]
        )
        
        result = await council.execute("Review code.py")
        
        analysis = result["results"]["step_0"]["parallel_results"]
        assert len(analysis) == 3
        assert "vulnerabilities" in analysis["security"]
        assert "optimize" in analysis["performance"]
        assert "docstrings" in analysis["style"]
        
        fix_result = result["results"]["step_1"]["parallel_results"]["fixer"]
        assert "optimized loop" in fix_result
        assert "added docstrings" in fix_result
    
    @pytest.mark.asyncio
    async def test_brainstorm_refine_decide_workflow(self):
        """Test brainstorm → refine → decide workflow."""
        # Brainstorm phase - generate many ideas
        brainstormers = []
        for i in range(3):
            agent = AgentWrapper(
                MockStrandsAgent(f"brainstormer{i}", f"Idea {i}: approach {i}"),
                name=f"brainstormer{i}"
            )
            brainstormers.append(agent)
        
        # Refine phase - improve top ideas
        refiner1 = AgentWrapper(
            MockStrandsAgent("refiner1", "Refined idea 0: detailed approach")
        )
        refiner2 = AgentWrapper(
            MockStrandsAgent("refiner2", "Refined idea 1: better approach")
        )
        
        # Decision phase - debate and choose
        decider1 = AgentWrapper(
            MockStrandsAgent("decider1", "Vote for refined idea 0")
        )
        decider2 = AgentWrapper(
            MockStrandsAgent("decider2", "Vote for refined idea 1")
        )
        moderator = AgentWrapper(
            MockStrandsAgent("moderator", "Refined idea 0 is best")
        )
        
        council = Council(
            name="brainstorm_workflow",
            steps=[
                ParallelStep(brainstormers),
                ParallelStep([refiner1, refiner2]),
                DebateStep([decider1, decider2], moderator=moderator, 
                          voting_strategy="moderator", rounds=1)
            ]
        )
        
        result = await council.execute("How to improve user engagement?")
        
        # Check all phases
        brainstorm = result["results"]["step_0"]["parallel_results"]
        assert len(brainstorm) == 3
        
        refined = result["results"]["step_1"]["parallel_results"]
        assert "Refined idea" in refined["refiner1"]
        
        decision = result["results"]["step_2"]
        assert decision["strategy"] == "moderator"
        assert "best" in decision["winner"]
    
    @pytest.mark.asyncio
    async def test_human_in_loop_workflow(self):
        """Test workflow with human approval step."""
        # AI agents propose solutions
        ai1 = AgentWrapper(MockStrandsAgent("ai1", "Automated solution A"))
        ai2 = AgentWrapper(MockStrandsAgent("ai2", "Automated solution B"))
        
        # Human reviews and decides
        human = HumanAgent(
            name="reviewer",
            input_handler=lambda p: "Approve solution A with modifications"
        )
        
        # AI implements human feedback
        implementer = AgentWrapper(
            MockStrandsAgent("implementer", "Implemented solution A with modifications")
        )
        
        council = Council(
            name="human_loop",
            steps=[
                ParallelStep([ai1, ai2]),
                ParallelStep([human]),
                ParallelStep([implementer])
            ]
        )
        
        result = await council.execute("Design new feature")
        
        # Verify human input was incorporated
        human_feedback = result["results"]["step_1"]["parallel_results"]["reviewer"]
        assert "Approve solution A" in human_feedback
        
        implementation = result["results"]["step_2"]["parallel_results"]["implementer"]
        assert "modifications" in implementation
    
    @pytest.mark.asyncio
    async def test_dynamic_scaling_workflow(self):
        """Test workflow that scales based on task complexity."""
        # Initial analyzer determines complexity
        analyzer = AgentWrapper(
            MockStrandsAgent("analyzer", "High complexity task")
        )
        
        # Dynamic split based on analysis
        template = MockStrandsAgent("worker", "Processed chunk")
        
        council = Council(
            name="dynamic_workflow",
            steps=[
                ParallelStep([analyzer]),
                SplitStep(
                    agent_template=template,
                    min_agents=2,
                    max_agents=5,
                    split_strategy="auto"
                )
            ]
        )
        
        # Long complex task
        complex_task = " ".join(["process"] * 100)
        result = await council.execute(complex_task)
        
        # Should have scaled up workers
        split_results = result["results"]["step_1"]["split_results"]
        assert len(split_results) > 2  # More than minimum
        assert all("Processed chunk" in r for r in split_results)
    
    @pytest.mark.asyncio
    async def test_iterative_refinement_workflow(self):
        """Test workflow with multiple refinement iterations."""
        # Initial draft
        drafter = AgentWrapper(
            MockStrandsAgent("drafter", "Initial draft v1")
        )
        
        # Multiple rounds of critique and revision
        critic = AgentWrapper(
            MockStrandsAgent("critic", "Needs improvement in section 2")
        )
        reviser = AgentWrapper(
            MockStrandsAgent("reviser", "Revised draft v2")
        )
        
        # Final approval
        approver = AgentWrapper(
            MockStrandsAgent("approver", "Approved final version")
        )
        
        council = Council(
            name="iterative_workflow",
            steps=[
                ParallelStep([drafter]),
                ParallelStep([critic]),
                ParallelStep([reviser]),
                ParallelStep([approver])
            ]
        )
        
        result = await council.execute("Write blog post")
        
        # Verify iterative process
        draft = result["results"]["step_0"]["parallel_results"]["drafter"]
        critique = result["results"]["step_1"]["parallel_results"]["critic"]
        revision = result["results"]["step_2"]["parallel_results"]["reviser"]
        approval = result["results"]["step_3"]["parallel_results"]["approver"]
        
        assert "v1" in draft
        assert "improvement" in critique
        assert "v2" in revision
        assert "Approved" in approval
    
    @pytest.mark.asyncio
    async def test_consensus_building_workflow(self):
        """Test workflow for building consensus among agents."""
        # Multiple stakeholders with different views
        stakeholders = []
        opinions = [
            "Strongly support option A",
            "Prefer option B",
            "Neutral between A and B",
            "Slight preference for A"
        ]
        
        for i, opinion in enumerate(opinions):
            agent = AgentWrapper(
                MockStrandsAgent(f"stakeholder{i}", opinion),
                name=f"stakeholder{i}"
            )
            stakeholders.append(agent)
        
        # Facilitator synthesizes consensus
        facilitator = AgentWrapper(
            MockStrandsAgent("facilitator", 
                           "Consensus: Majority lean towards A with B considerations")
        )
        
        council = Council(
            name="consensus_workflow",
            steps=[
                ParallelStep(stakeholders),
                ParallelStep([facilitator])
            ]
        )
        
        result = await council.execute("Choose between option A and B")
        
        # Verify all opinions gathered
        opinions_result = result["results"]["step_0"]["parallel_results"]
        assert len(opinions_result) == 4
        
        # Verify consensus reached
        consensus = result["results"]["step_1"]["parallel_results"]["facilitator"]
        assert "Consensus" in consensus
        assert "Majority" in consensus