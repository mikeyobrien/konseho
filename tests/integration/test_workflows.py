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
from konseho.factories import CouncilFactory
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
        
        factory = CouncilFactory()
        council = factory.create_council(
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
        
        # Verify data flow - results are now StepResult objects
        step0_result = result["results"]["step_0"]
        research_results = step0_result.metadata["parallel_results"]
        assert "Found data about X" in research_results["researcher1"]
        assert "Found data about Y" in research_results["researcher2"]
    
    @pytest.mark.asyncio
    async def test_code_review_workflow(self):
        """Test code analysis → review → fix workflow."""
        # Analyze code in parallel
        security_analyzer = AgentWrapper(
            MockStrandsAgent("security", "No vulnerabilities found"),
            name="security"
        )
        performance_analyzer = AgentWrapper(
            MockStrandsAgent("performance", "Could optimize loop at line 42"),
            name="performance"
        )
        style_analyzer = AgentWrapper(
            MockStrandsAgent("style", "Missing docstrings"),
            name="style"
        )
        
        # Code fixer based on analysis
        fixer = AgentWrapper(
            MockStrandsAgent("fixer", "Fixed: optimized loop, added docstrings"),
            name="fixer"
        )
        
        factory = CouncilFactory()
        council = factory.create_council(
            name="code_review",
            steps=[
                ParallelStep([security_analyzer, performance_analyzer, style_analyzer]),
                ParallelStep([fixer])
            ]
        )
        
        result = await council.execute("Review code.py")
        
        step0_result = result["results"]["step_0"]
        analysis = step0_result.metadata["parallel_results"]
        assert len(analysis) == 3
        assert "vulnerabilities" in analysis["security"]
        assert "optimize" in analysis["performance"]
        assert "docstrings" in analysis["style"]
        
        step1_result = result["results"]["step_1"]
        fix_result = step1_result.metadata["parallel_results"]["fixer"]
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
            MockStrandsAgent("refiner1", "Refined idea 0: detailed approach"),
            name="refiner1"
        )
        refiner2 = AgentWrapper(
            MockStrandsAgent("refiner2", "Refined idea 1: better approach"),
            name="refiner2"
        )
        
        # Decision phase - debate and choose
        decider1 = AgentWrapper(
            MockStrandsAgent("decider1", "Vote for refined idea 0"),
            name="decider1"
        )
        decider2 = AgentWrapper(
            MockStrandsAgent("decider2", "Vote for refined idea 1"),
            name="decider2"
        )
        moderator = AgentWrapper(
            MockStrandsAgent("moderator", "Refined idea 0 is best"),
            name="moderator"
        )
        
        factory = CouncilFactory()
        council = factory.create_council(
            name="brainstorm_workflow",
            steps=[
                ParallelStep(brainstormers),
                ParallelStep([refiner1, refiner2]),
                DebateStep([decider1, decider2], moderator=moderator, 
                          voting_strategy="moderator", rounds=1)
            ]
        )
        
        result = await council.execute("How to improve user engagement?")
        
        # Check all phases - results are now StepResult objects
        step0_result = result["results"]["step_0"]
        brainstorm = step0_result.metadata["parallel_results"]
        assert len(brainstorm) == 3
        
        step1_result = result["results"]["step_1"]
        refined = step1_result.metadata["parallel_results"]
        assert "Refined idea" in refined["refiner1"]
        
        step2_result = result["results"]["step_2"]
        assert "moderator" in step2_result.metadata["strategy"]
        # The output is the winning agent's response, not the moderator's
        assert "Vote for refined idea" in step2_result.output
    
    @pytest.mark.asyncio
    async def test_human_in_loop_workflow(self):
        """Test workflow with human approval step."""
        # AI agents propose solutions
        ai1 = AgentWrapper(MockStrandsAgent("ai1", "Automated solution A"), name="ai1")
        ai2 = AgentWrapper(MockStrandsAgent("ai2", "Automated solution B"), name="ai2")
        
        # Human reviews and decides
        human = HumanAgent(
            name="reviewer",
            input_handler=lambda p: "Approve solution A with modifications"
        )
        
        # AI implements human feedback
        implementer = AgentWrapper(
            MockStrandsAgent("implementer", "Implemented solution A with modifications"),
            name="implementer"
        )
        
        factory = CouncilFactory()
        council = factory.create_council(
            name="human_loop",
            steps=[
                ParallelStep([ai1, ai2]),
                ParallelStep([human]),
                ParallelStep([implementer])
            ]
        )
        
        result = await council.execute("Design new feature")
        
        # Verify human input was incorporated - results are StepResult objects
        step1_result = result["results"]["step_1"]
        human_feedback = step1_result.metadata["parallel_results"]["reviewer"]
        assert "Approve solution A" in human_feedback
        
        step2_result = result["results"]["step_2"]
        implementation = step2_result.metadata["parallel_results"]["implementer"]
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
        
        factory = CouncilFactory()
        council = factory.create_council(
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
        
        # Should have scaled up workers - results are StepResult objects
        step1_result = result["results"]["step_1"]
        split_results = step1_result.metadata["split_results"]
        assert len(split_results) > 2  # More than minimum
        assert all("Processed chunk" in r for r in split_results)
    
    @pytest.mark.asyncio
    async def test_iterative_refinement_workflow(self):
        """Test workflow with multiple refinement iterations."""
        # Initial draft
        drafter = AgentWrapper(
            MockStrandsAgent("drafter", "Initial draft v1"),
            name="drafter"
        )
        
        # Multiple rounds of critique and revision
        critic = AgentWrapper(
            MockStrandsAgent("critic", "Needs improvement in section 2"),
            name="critic"
        )
        reviser = AgentWrapper(
            MockStrandsAgent("reviser", "Revised draft v2"),
            name="reviser"
        )
        
        # Final approval
        approver = AgentWrapper(
            MockStrandsAgent("approver", "Approved final version"),
            name="approver"
        )
        
        factory = CouncilFactory()
        council = factory.create_council(
            name="iterative_workflow",
            steps=[
                ParallelStep([drafter]),
                ParallelStep([critic]),
                ParallelStep([reviser]),
                ParallelStep([approver])
            ]
        )
        
        result = await council.execute("Write blog post")
        
        # Verify iterative process - results are StepResult objects
        step0_result = result["results"]["step_0"]
        draft = step0_result.metadata["parallel_results"]["drafter"]
        
        step1_result = result["results"]["step_1"]
        critique = step1_result.metadata["parallel_results"]["critic"]
        
        step2_result = result["results"]["step_2"]
        revision = step2_result.metadata["parallel_results"]["reviser"]
        
        step3_result = result["results"]["step_3"]
        approval = step3_result.metadata["parallel_results"]["approver"]
        
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
                           "Consensus: Majority lean towards A with B considerations"),
            name="facilitator"
        )
        
        factory = CouncilFactory()
        council = factory.create_council(
            name="consensus_workflow",
            steps=[
                ParallelStep(stakeholders),
                ParallelStep([facilitator])
            ]
        )
        
        result = await council.execute("Choose between option A and B")
        
        # Verify all opinions gathered - results are StepResult objects
        step0_result = result["results"]["step_0"]
        opinions_result = step0_result.metadata["parallel_results"]
        assert len(opinions_result) == 4
        
        # Verify consensus reached
        step1_result = result["results"]["step_1"]
        consensus = step1_result.metadata["parallel_results"]["facilitator"]
        assert "Consensus" in consensus
        assert "Majority" in consensus