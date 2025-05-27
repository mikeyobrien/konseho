"""Tests for PersonaTemplate with tools support."""


from konseho.dynamic.persona_registry import PersonaRegistry, PersonaTemplate


def mock_tool_1(x: str) -> str:
    """Mock tool 1."""
    return f"tool1: {x}"


def mock_tool_2(x: str) -> str:
    """Mock tool 2."""
    return f"tool2: {x}"


def mock_tool_3(x: str) -> str:
    """Mock tool 3."""
    return f"tool3: {x}"


class TestPersonaTemplate:
    """Test PersonaTemplate with tools."""
    
    def test_persona_template_with_empty_tools(self):
        """Test creating persona with no tools."""
        persona = PersonaTemplate(
            name="Test Persona",
            category="test",
            expertise=["testing"],
            personality="analytical",
            description="A test persona",
            system_prompt="You are a test.",
            temperature=0.7,
            tools=[]
        )
        
        assert persona.name == "Test Persona"
        assert persona.tools == []
        assert persona.temperature == 0.7
    
    def test_persona_template_with_tools(self):
        """Test creating persona with tools."""
        tools = [mock_tool_1, mock_tool_2]
        
        persona = PersonaTemplate(
            name="Tool User",
            category="technical",
            expertise=["tools", "automation"],
            personality="pragmatic",
            description="A persona that uses tools",
            system_prompt="You are a tool user.",
            temperature=0.5,
            tools=tools
        )
        
        assert persona.name == "Tool User"
        assert len(persona.tools) == 2
        assert mock_tool_1 in persona.tools
        assert mock_tool_2 in persona.tools
        assert persona.tools[0]("test") == "tool1: test"
    
    def test_persona_template_default_tools(self):
        """Test that tools default to empty list."""
        persona = PersonaTemplate(
            name="No Tools",
            category="general",
            expertise=["general"],
            personality="neutral",
            description="A persona without tools",
            system_prompt="You have no tools."
        )
        
        assert persona.tools == []
        assert isinstance(persona.tools, list)
    
    def test_persona_tools_are_mutable(self):
        """Test that each persona gets its own tools list."""
        persona1 = PersonaTemplate(
            name="Persona 1",
            category="test",
            expertise=["test"],
            personality="test",
            description="Test 1",
            system_prompt="Test 1"
        )
        
        persona2 = PersonaTemplate(
            name="Persona 2",
            category="test",
            expertise=["test"],
            personality="test",
            description="Test 2",
            system_prompt="Test 2"
        )
        
        # Modify persona1's tools
        persona1.tools.append(mock_tool_1)
        
        # persona2's tools should be unaffected
        assert len(persona1.tools) == 1
        assert len(persona2.tools) == 0


class TestPersonaRegistryWithTools:
    """Test PersonaRegistry with tool-enabled personas."""
    
    def test_register_persona_with_tools(self):
        """Test registering personas with tools."""
        registry = PersonaRegistry()
        
        # Clear default personas for testing
        registry.personas.clear()
        
        # Register persona with tools
        persona = PersonaTemplate(
            name="Tooled Expert",
            category="technical",
            expertise=["automation"],
            personality="efficient",
            description="Uses tools effectively",
            system_prompt="You use tools.",
            temperature=0.6,
            tools=[mock_tool_1, mock_tool_2]
        )
        
        registry.register(persona)
        
        retrieved = registry.get_persona("Tooled Expert")
        assert retrieved is not None
        assert len(retrieved.tools) == 2
        assert mock_tool_1 in retrieved.tools
    
    def test_get_personas_preserves_tools(self):
        """Test that getting personas preserves their tools."""
        registry = PersonaRegistry()
        registry.personas.clear()
        
        # Register multiple personas with different tools
        personas = [
            PersonaTemplate(
                name="Explorer",
                category="research",
                expertise=["exploration"],
                personality="curious",
                description="Explores",
                system_prompt="Explore",
                tools=[mock_tool_1]
            ),
            PersonaTemplate(
                name="Builder",
                category="technical",
                expertise=["building"],
                personality="constructive",
                description="Builds",
                system_prompt="Build",
                tools=[mock_tool_2, mock_tool_3]
            ),
            PersonaTemplate(
                name="Thinker",
                category="analytical",
                expertise=["thinking"],
                personality="thoughtful",
                description="Thinks",
                system_prompt="Think",
                tools=[]
            )
        ]
        
        for p in personas:
            registry.register(p)
        
        # Test get_personas_by_category preserves tools
        technical = registry.get_personas_by_category("technical")
        assert len(technical) == 1
        assert len(technical[0].tools) == 2
        
        # Test get_all_personas preserves tools
        all_personas = registry.get_all_personas()
        assert len(all_personas) == 3
        
        # Find each persona and check tools
        explorer = next(p for p in all_personas if p.name == "Explorer")
        builder = next(p for p in all_personas if p.name == "Builder")
        thinker = next(p for p in all_personas if p.name == "Thinker")
        
        assert len(explorer.tools) == 1
        assert len(builder.tools) == 2
        assert len(thinker.tools) == 0