# services/completion_service.py

from langchain_core.runnables.history import RunnableWithMessageHistory
from langchain.agents import create_tool_calling_agent, AgentExecutor
from flask import current_app as app, g
from blueprints.api.v2.models.ChatAssistants import ChatAssistantModel
from blueprints.api.v2.models.Providers import ProviderModel
from utils.vector_store import get_vector_store
from utils.llm import (
    init_model,
    init_embeddings,
    get_template,
    get_chat_history,
    format_error,
    save_chat_history_to_db,
    cut_chat_history,
    add_llm_tools,
)


class CompletionService:
    def __init__(self, workspace_sid, session_id):
        self.workspace_sid = workspace_sid
        self.session_id = session_id

    def apply_overrides(self, original, overrides):
        updated = original.copy()
        for key, value in vars(overrides).items():
            if key in original and value is not None:
                updated[key] = value
        return updated

    def process_completion(self, assistantID, data):
        records = ChatAssistantModel.get(
            {"workspace_sid": self.workspace_sid, "sid": assistantID}
        )

        if not records:
            return 404, "Assistant not found!"

        assistant = ChatAssistantModel.to_dict(records[0])
        system_prompt = assistant["model"]["system_prompt"]
        created_args = {
            "model": assistant["model"]["model"],
            "api_key": assistant["model"]["provider"]["api_key"],
            "base_url": assistant["model"]["provider"]["address"],
        }

        if assistant["model"]["provider"]["source"] == "cohere":
            created_args["cohere_api_key"] = created_args["api_key"]
            del created_args["api_key"]

        if assistant["model"].get("temperature"):
            created_args["temperature"] = assistant["model"]["temperature"]

        if assistant["model"].get("max_tokens"):
            created_args["max_tokens"] = assistant["model"]["max_tokens"]

        if hasattr(data, "overrides") and data.overrides:
            created_args = self.apply_overrides(created_args, data.overrides)

        result, llm = init_model(
            assistant["model"]["provider"]["source"], **created_args
        )

        if not result:
            return 500, llm

        tools = []

        if assistant["model"].get("knowledge_base"):
            try:
                provider = ProviderModel.get(assistant["model"]["provider_sid"])
                created_args = {
                    "api_key": provider.api_key,
                    "base_url": provider.address,
                }

                if provider.source == "ollama":
                    created_args["model"] = assistant["model"]["model"]
                    del created_args["api_key"]

                elif provider.source == "cohere":
                    created_args["cohere_api_key"] = provider.api_key
                    created_args["model"] = "embed-english-v3.0"
                    del created_args["api_key"]

                if hasattr(data, "overrides") and data.overrides:
                    created_args = self.apply_overrides(created_args, data.overrides)

                result, embeddings = init_embeddings(provider.source, **created_args)
            except Exception as e:
                app.logger.error(
                    f"Completion service error: {str(e)}",
                    exc_info=app.config["DEBUG_APP"],
                )
                return 500, "Internal server error"

            knowledge_base = get_vector_store(
                assistant["workspace_sid"], assistant["sid"], embeddings
            )
            tools.append(knowledge_base)

        assistant_tools = assistant["model"].get("tools")

        if (
            hasattr(data, "overrides")
            and data.overrides
            and hasattr(data.overrides, "tools")
        ):
            assistant_tools = data.overrides.tools

        if assistant_tools:
            tools = add_llm_tools(tools, assistant_tools)

        if tools:
            agent = create_tool_calling_agent(
                llm=llm,
                tools=tools,
                prompt=get_template(system_prompt, "tools"),
            )
            chain = AgentExecutor(agent=agent, tools=tools, verbose=True)
        else:
            chain = get_template(system_prompt) | llm

        chain_with_history = RunnableWithMessageHistory(
            chain,
            get_chat_history,
            input_messages_key="query",
            history_messages_key="history",
        )

        try:
            response = chain_with_history.invoke(
                {"query": data.message},
                config={"configurable": {"session_id": self.session_id}},
            )
        except Exception as e:
            error_code, error = format_error(
                assistant["model"]["provider"]["source"], e
            )
            app.logger.error(
                f"Completion service error: {error_code} {error}",
                exc_info=app.config["DEBUG_APP"],
            )

            return error_code, error

        g.chat_history.messages = cut_chat_history(
            g.chat_history.messages, data.max_history
        )

        save_chat_history_to_db(self.session_id, g.chat_history.messages)
        output = response["output"] if tools else response.content
        return 200, output
