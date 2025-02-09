import asyncio
from autogen_agentchat.agents import AssistantAgent
from autogen_agentchat.conditions import TextMentionTermination
from autogen_agentchat.teams import RoundRobinGroupChat
from autogen_core import CancellationToken
from autogen_ext.models.openai import OpenAIChatCompletionClient
import sys

class AITeamManager:
    def __init__(self):
        """
        Initialize the AI Team Manager with Ollama using Mistral
        """
        # Initialize Ollama client using OpenAIChatCompletionClient with Mistral
        self.model_client = OpenAIChatCompletionClient(
            model="mistral:latest",
            base_url="http://localhost:11434/v1",
            api_key="placeholder",
            model_info={
                "vision": False,
                "function_calling": True,
                "json_output": False,
                "family": "unknown",
            },
        )
        
        # Initialize agents
        self.researcher = AssistantAgent(
            "researcher",
            model_client=self.model_client,
            system_message="""You are a research expert. Your role is to:
            1. Analyze information
            2. Identify key points
            3. Provide detailed research insights
            When you finish your analysis, explain your findings."""
        )

        self.analyst = AssistantAgent(
            "analyst",
            model_client=self.model_client,
            system_message="""You are a data analyst. Your role is to:
            1. Review the research findings
            2. Analyze patterns and trends
            3. Draw meaningful conclusions
            Respond with 'CONTINUE' if more analysis is needed, or 'COMPLETE' if analysis is sufficient."""
        )

        self.writer = AssistantAgent(
            "writer",
            model_client=self.model_client,
            system_message="""You are a professional writer. Your role is to:
            1. Take the research and analysis
            2. Create clear and concise summaries
            3. Present information in an engaging way
            Respond with 'APPROVE' when the final output is ready."""
        )

        # Set up team
        self.text_termination = TextMentionTermination("APPROVE")
        self.team = RoundRobinGroupChat(
            [self.researcher, self.analyst, self.writer],
            termination_condition=self.text_termination
        )

    async def process_task(self, task: str):
        """
        Process a given task using the AI team.
        
        Args:
            task (str): The task or text to be analyzed
        """
        try:
            print(f"\nProcessing task: {task}\n")
            print("Team analysis starting...\n")

            async for message in self.team.run_stream(task=task):
                if hasattr(message, 'content'):
                    print(f"\n{message.source}: {message.content}")
                else:
                    print("\nTask Result:", message)

            print("\nTeam analysis completed.")
            
        except Exception as e:
            print(f"An error occurred: {str(e)}")
            raise

async def main():
    # Create team manager instance
    team_manager = AITeamManager()
    
    # Example task
    task = """Analyze this text and provide insights: 
    'AI technology has evolved significantly in recent years, 
    with major breakthroughs in natural language processing and computer vision.'"""
    
    # Process the task
    await team_manager.process_task(task)

if __name__ == "__main__":
    # Make sure Ollama is running first with Mistral model!
    asyncio.run(main())