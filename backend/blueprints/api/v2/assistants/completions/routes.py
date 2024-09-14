from apiflask import APIBlueprint
from flask import g, current_app as app
from models.Response import Response as ApiResponse
from models.OpenAiClient import OpenAiClient
from utils.views import APIAuthenticatedMethodView
from blueprints.api.v2.schemas.Completions import CompletionCreate
from blueprints.api.v2.models.ChatAssistants import ChatAssistantModel
from blueprints.api.v2.models.Providers import ProviderModel
from langchain_core.runnables.history import RunnableWithMessageHistory
from langchain.agents import create_tool_calling_agent
from langchain.agents import AgentExecutor
from decorators.Session import check_session_cookie
from utils.vector_store import get_vector_store
from utils.llm import (
    init_model,
    init_embeddings,
    get_template,
    get_chat_history,
    format_openai_error,
    save_chat_history_to_db,
    cut_chat_history,
    get_session_prefix,
    add_llm_tools,
)


from utils.session_utils import save_session, get_session

# from blueprints.api.v2.schemas.Completions import CompletionCreateSession

api_v2_completions_bp = APIBlueprint("api_v2_completions_bp", __name__)


class Completion(APIAuthenticatedMethodView):

    @api_v2_completions_bp.input(CompletionCreate.Schema, arg_name="data")
    # @api_v2_completions_bp.input(
    #    CompletionCreateSession.Schema, location="header", arg_name="header"
    # )
    @api_v2_completions_bp.doc(tags=["Completions"], security="ApiKeyAuth")
    @check_session_cookie
    def post(self, assistantID, data: CompletionCreate):

        records = ChatAssistantModel.get(
            {"workspace_sid": g.api_key.workspace_sid, "sid": assistantID}
        )

        if len(records) == 0:
            payload_response = ApiResponse.payload_v2(404, "Assistant not found!")
            return ApiResponse.output(payload_response)

        assistant = ChatAssistantModel.to_dict(records[0])

        created_args = {}
        created_args["model"] = assistant["model"]["model"]
        created_args["api_key"] = assistant["model"]["provider"]["api_key"]
        created_args["base_url"] = assistant["model"]["provider"]["address"]

        if assistant["model"]["temperature"]:
            created_args["temperature"] = assistant["model"]["temperature"]

        if assistant["model"]["max_tokens"]:
            created_args["max_tokens"] = assistant["model"]["max_tokens"]

        result, llm = init_model(
            assistant["model"]["provider"]["source"], **created_args
        )

        if not result:
            payload_response = ApiResponse.payload_v2(500, llm)
            return ApiResponse.output(payload_response)

        tools = []

        if len(assistant["model"]["knowledge_base"]) > 0:
            try:
                provider = ProviderModel.get(assistant["model"]["provider_sid"])
                created_args = {}
                created_args["api_key"] = provider.api_key
                created_args["base_url"] = provider.address

                if provider.source == "ollama":
                    created_args["model"] = assistant["model"]["model"]
                    del created_args["api_key"]

                result, embeddings = init_embeddings(provider.source, **created_args)
            except Exception as e:
                app.logger.error(f"Error: {str(e)}")
                payload_response = ApiResponse.payload_v2(500, "Internal server error")
                return ApiResponse.output(payload_response)

            knowledge_base = get_vector_store(
                assistant["workspace_sid"], assistant["sid"], embeddings
            )
            tools.append(knowledge_base)

        # print("DDDDDDDDDDDDDDDDDDDDDDDDDDD")
        # print("DDDDDDDDDDDDDDDDDDDDDDDDDDD")
        # print("DDDDDDDDDDDDDDDDDDDDDDDDDDD")
        # print(assistant["model"])

        if len(assistant["model"]["tools"]) > 0:
            tools = add_llm_tools(tools, assistant["model"]["tools"])

            # print("WWWWWWWWWWWWWWWWWWWWWWWWWW")
            # print("WWWWWWWWWWWWWWWWWWWWWWWWWW")
            # print("WWWWWWWWWWWWWWWWWWWWWWWWWW")
            # print(tools)
            # return

        if len(tools) > 0:
            agent = create_tool_calling_agent(
                llm=llm,
                tools=tools,
                prompt=get_template(assistant["model"]["system_prompt"], "tools"),
            )
            chain = AgentExecutor(agent=agent, tools=tools, verbose=True)
        else:
            chain = get_template(assistant["model"]["system_prompt"]) | llm

        chain_with_history = RunnableWithMessageHistory(
            chain,
            get_chat_history,
            input_messages_key="query",
            history_messages_key="history",
        )

        try:
            response = chain_with_history.invoke(
                {"query": data.message},
                config={
                    "configurable": {"session_id": g.session_id},
                    # "callbacks": [MyCustomHandler()],
                },
            )

        except Exception as e:

            if assistant["model"]["provider"]["source"] == "openai":
                error = format_openai_error(e)
                error_code = 500
            else:
                error = str(e)
                error_code = 500

            app.logger.error(
                f"Exception occured:  {error}", exc_info=app.config.get("DEBUG_APP")
            )
            payload_response = ApiResponse.payload_v2(
                error_code,
                error,
            )
            return ApiResponse.output(
                payload_response, cookies=[{"session_id": g.session_id}]
            )

        # print("DDDDDDDDDDDDDDDDDDDDDDDDd")
        # print(g.chat_history.messages)
        # print("DDDDDDDDDDDDDDDDDDDDDDDDd")
        g.chat_history.messages = cut_chat_history(g.chat_history.messages, 20)
        session_id = get_session_prefix(g.session_id)
        save_chat_history_to_db(session_id, g.chat_history.messages)
        output = response["output"] if len(tools) > 0 else response.content
        payload_response = ApiResponse.payload_v2(
            200,
            "Completion request was successful!",
            output,
        )
        return ApiResponse.output(
            payload_response, cookies=[{"session_id": g.session_id}]
        )


api_v2_completions_bp.add_url_rule(
    "/completions/<assistantID>", view_func=Completion.as_view("completion")
)
