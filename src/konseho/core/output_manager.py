"""Output management for saving council execution results."""

import hashlib
import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any


class OutputManager:
    """Manages saving and loading of council execution outputs."""
    
    def __init__(self, base_dir: str | Path = "council_outputs"):
        """Initialize output manager.
        
        Args:
            base_dir: Base directory for saving outputs
        """
        self.base_dir = Path(base_dir)
        self.base_dir.mkdir(parents=True, exist_ok=True)
        
    def save_output(
        self,
        task: str,
        result: dict[str, Any],
        council_name: str = "Council",
        metadata: dict[str, Any] | None = None,
        filename: str | None = None
    ) -> Path:
        """Save council output to a file.
        
        Args:
            task: The task/query that was executed
            result: The execution result dictionary
            council_name: Name of the council
            metadata: Additional metadata to save
            filename: Optional custom filename (without extension)
            
        Returns:
            Path to the saved file
        """
        # Create subdirectory for the council
        council_dir = self.base_dir / council_name.replace(" ", "_").lower()
        council_dir.mkdir(exist_ok=True)
        
        # Generate filename if not provided
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            task_hash = hashlib.md5(task.encode()).hexdigest()[:8]
            filename = f"{timestamp}_{task_hash}"
        
        # Prepare output data
        output_data = {
            "task": task,
            "council_name": council_name,
            "timestamp": datetime.now().isoformat(),
            "result": result,
            "metadata": metadata or {}
        }
        
        # Save as JSON
        output_path = council_dir / f"{filename}.json"
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(output_data, f, indent=2, ensure_ascii=False)
        
        return output_path
    
    def save_formatted_output(
        self,
        task: str,
        result: dict[str, Any],
        council_name: str = "Council",
        metadata: dict[str, Any] | None = None,
        filename: str | None = None
    ) -> Path:
        """Save council output in a human-readable format.
        
        Args:
            task: The task/query that was executed
            result: The execution result dictionary
            council_name: Name of the council
            metadata: Additional metadata to save
            filename: Optional custom filename (without extension)
            
        Returns:
            Path to the saved file
        """
        # Create subdirectory for the council
        council_dir = self.base_dir / council_name.replace(" ", "_").lower()
        council_dir.mkdir(exist_ok=True)
        
        # Generate filename if not provided
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            task_hash = hashlib.md5(task.encode()).hexdigest()[:8]
            filename = f"{timestamp}_{task_hash}"
        
        # Format the output
        output_lines = [
            "COUNCIL EXECUTION REPORT",
            f"{'=' * 80}",
            f"Council: {council_name}",
            f"Task: {task}",
            f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            f"{'=' * 80}\n"
        ]
        
        # Add metadata if present
        if metadata:
            output_lines.append("METADATA:")
            for key, value in metadata.items():
                output_lines.append(f"  {key}: {value}")
            output_lines.append("")
        
        # Format results based on structure
        if 'results' in result:
            for step_name, step_data in result['results'].items():
                output_lines.append(f"\n{step_name.upper()}")
                output_lines.append("-" * 40)
                
                # Handle different step types
                if isinstance(step_data, dict):
                    if 'parallel_results' in step_data:
                        # Parallel step results
                        for agent_name, agent_result in step_data['parallel_results'].items():
                            output_lines.append(f"\n[{agent_name}]:")
                            output_lines.append(self._format_agent_result(agent_result))
                    elif 'winner' in step_data:
                        # Debate step results
                        output_lines.append(f"\nWinner: {step_data.get('winner', 'N/A')}")
                        if 'proposals' in step_data:
                            output_lines.append("\nProposals:")
                            proposals = step_data['proposals']
                            if isinstance(proposals, dict):
                                # Proposals are stored as agent_name: content pairs
                                for agent_name, content in proposals.items():
                                    output_lines.append(f"\n[{agent_name}]:")
                                    # Handle string content (might be JSON string)
                                    if isinstance(content, str):
                                        try:
                                            # Try to parse if it's a JSON string
                                            parsed = json.loads(content)
                                            if isinstance(parsed, list) and len(parsed) > 0 and isinstance(parsed[0], dict):
                                                text = parsed[0].get('text', str(parsed))
                                            else:
                                                text = str(parsed)
                                        except:
                                            text = content
                                    else:
                                        text = str(content)
                                    output_lines.append(text[:500] + "..." if len(text) > 500 else text)
                    else:
                        # Generic step result
                        output_lines.append(str(step_data))
        
        # Add summary if available
        if 'data' in result:
            output_lines.append(f"\n{'=' * 80}")
            output_lines.append("SUMMARY DATA:")
            output_lines.append(json.dumps(result['data'], indent=2))
        
        # Save as text file
        output_path = council_dir / f"{filename}.txt"
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write('\n'.join(output_lines))
        
        # Also save the JSON version
        json_path = council_dir / f"{filename}.json"
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump({
                "task": task,
                "council_name": council_name,
                "timestamp": datetime.now().isoformat(),
                "result": result,
                "metadata": metadata or {}
            }, f, indent=2, ensure_ascii=False)
        
        return output_path
    
    def _format_agent_result(self, agent_result: Any) -> str:
        """Format an individual agent's result."""
        # If it's already a string, return it
        if isinstance(agent_result, str):
            return agent_result
            
        # If it's a dict with content structure
        if isinstance(agent_result, dict) and 'content' in agent_result:
            content = agent_result['content']
            if isinstance(content, list) and len(content) > 0:
                # Check if the first item is a dict
                if isinstance(content[0], dict) and 'text' in content[0]:
                    return content[0]['text']
                # If it's already text, return it
                elif isinstance(content[0], str):
                    return content[0]
                    
        return str(agent_result)
    
    def list_outputs(self, council_name: str | None = None) -> list[dict[str, Any]]:
        """List all saved outputs.
        
        Args:
            council_name: Optional filter by council name
            
        Returns:
            List of output metadata
        """
        outputs = []
        
        # Determine which directories to search
        if council_name:
            search_dirs = [self.base_dir / council_name.replace(" ", "_").lower()]
        else:
            search_dirs = [d for d in self.base_dir.iterdir() if d.is_dir()]
        
        for council_dir in search_dirs:
            if not council_dir.exists():
                continue
                
            for json_file in council_dir.glob("*.json"):
                try:
                    with open(json_file) as f:
                        data = json.load(f)
                        outputs.append({
                            "file": str(json_file),
                            "task": data.get("task", ""),
                            "council_name": data.get("council_name", ""),
                            "timestamp": data.get("timestamp", ""),
                            "has_text": (json_file.with_suffix('.txt')).exists()
                        })
                except Exception:
                    continue
        
        # Sort by timestamp
        outputs.sort(key=lambda x: x["timestamp"], reverse=True)
        return outputs
    
    def load_output(self, filepath: str | Path) -> dict[str, Any]:
        """Load a saved output file.
        
        Args:
            filepath: Path to the output file
            
        Returns:
            The loaded output data
        """
        with open(filepath) as f:
            return json.load(f)
    
    def cleanup_old_outputs(self, days: int = 30):
        """Remove outputs older than specified days.
        
        Args:
            days: Number of days to keep outputs
        """
        cutoff_date = datetime.now() - timedelta(days=days)
        
        for council_dir in self.base_dir.iterdir():
            if not council_dir.is_dir():
                continue
                
            for json_file in council_dir.glob("*.json"):
                try:
                    with open(json_file) as f:
                        data = json.load(f)
                        timestamp = datetime.fromisoformat(data.get("timestamp", ""))
                        
                    if timestamp < cutoff_date:
                        json_file.unlink()
                        # Also remove text file if exists
                        txt_file = json_file.with_suffix('.txt')
                        if txt_file.exists():
                            txt_file.unlink()
                except Exception:
                    continue