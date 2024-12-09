# Same application in three ways: An AI travel assistant

This project serves as an investigation of multiple methodologies for implementing an AI assistant. This assistant provides useful answers to travel-related queries.

Getting started with large language modelling and generative AI can be overwhelming due to the wide variety of tools, techniques and methods available. A practical approach to learning is to focus on a straightforward use case and build models from scratch. 

This project is designed as a starting point, providing a learning experience for beginners in the field. Here, the same application has been implemented using three approaches.

## Implementation approaches
1. **Basic**: A non-agentic framework that uses [chat completions](https://platform.openai.com/docs/guides/text-generation) API from OpenAI and tool calling.
2. **Agent method**: An multi-agent framework based on chat completions API and tool calling.
3. **LangGraph single-agent**: A single-agent graph framework with tool calling implemented using [LangChain](https://python.langchain.com/docs/introduction/) and [LangGraph](https://langchain-ai.github.io/langgraph/).
4. **LangGraph multi-agent**: INCOMPLETE. A supervisor-worker graph framework.

## Queries handled by the assistant
1. Travel duration given the origin, destination and mode of travel.
2. Traffic updates for a given route
3. Transit route numbers for a given trip.
4. Transit schedule for a route number.
5. Other travel-related queries (the assistant decides which queries are relevant).

## Requirements
- python 3.7+
- openai
- langchain
- langgraph
- pydantic
- requests (if calling Google maps API)
- langsmith (for evaluation)
- python-dotenv (for environment variable management)

## Installation

1. **Clone the repository**

    ```bash
    git clone https://github.com/buddhiW/travel_duration_assistant_2.git
    cd travel_duration_assistant
    ```

2. **Install dependencies**

    ```bash
    pip install -r requirements.txt
    ```

3. **Setup API keys**

    - Obtain an API key from OpenAI.
    - Obtain an API key from LangChain.
    - Create a `.env` file in the root directory and add the API keys:

    ```
    OPENAI_API_KEY=your_openai_api_key
    LANGCHAIN_API_KEY=your_langchain_api_key
    ```
    This project uses OpenAI's `gpt-4` models. However, you can experiment with other models.

## Usage

    Navigate to the folder corresponding to each approach within the `core` folder and execute main.py

    ```bash
    python main.py
    ```  

    `questions` list in main.py is a sample list of questions you can use to test the applications.

 

## References
1. [Tool calling and multi-agent framework with Chat Completions API](https://cookbook.openai.com/examples/orchestrating_agents?utm_source=www.therundown.ai&utm_medium=newsletter&utm_campaign=anthropic-ceo-predicts-ai-utopia&_bhlid=db30852b7747db2f62cd8fde276efcf151c6c21a)
2. [LangGraph introductory tutorial](https://langchain-ai.github.io/langgraph/tutorials/introduction/)
3. [Message history with LangGraph](https://python.langchain.com/docs/how_to/message_history/)
4. [Multi-agent supervisor using LangGraph](https://github.com/langchain-ai/langgraph/blob/main/docs/docs/tutorials/multi_agent/agent_supervisor.ipynb)
5. [Customer support bot using LangGraph](https://langchain-ai.github.io/langgraph/tutorials/customer-support/customer-support/)