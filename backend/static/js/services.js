APP.services = {
  completion: async function (message, { signal }) {
    APP.debug.log("messageInput", message);
    try {
      const response = await fetch(
        `${APP.config.api_baseurl}${APP.config.services_endpoints.completion}/${APP.agentID}`,
        {
          method: "POST",
          headers: {
            accept: "application/json",
            "X-Session-Id": APP.session.sessionId,
            "Content-Type": "application/json",
          },
          body: JSON.stringify({
            message: message,
            max_history: APP.config.max_history,
            overrides: null,
          }),
          signal: signal,
        }
      );
      APP.debug.log("Completion response: ", response);
      if (response.ok) {
        const completion = await response.json();
        if (completion && completion.data) {
          return {
            status: 200,
            message: completion.data,
          };
        } else {
          const msg = "No response from server.";
          APP.debug.error(msg, response.statusText);
          if (APP.error_message) {
            APP.appendAgentMessage(APP.error_message);
          }
          return {
            status: 500,
            data: msg,
          };
        }
      } else {
        const msg = "Error communicating with server.";
        APP.debug.error(msg, response.statusText);
        if (APP.error_message) {
          APP.appendAgentMessage(APP.error_message);
        }
        return {
          status: 500,
          data: msg,
        };
      }
    } catch (error) {
      if (error == "Aborted by the user") {
        return {
          status: 499,
          data: error,
        };
      }
      const msg = "Error communicating with server: ";
      if (APP.error_message) {
        APP.appendAgentMessage(APP.error_message);
      }
      APP.debug.error(msg, error);
    }
  },
};
