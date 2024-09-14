APP.elements = {
  _chatWindow: document.getElementById("chat-window"),
  _messageInput: document.getElementById("message-input"),
  _scrollToBottom: document.getElementById("scrollToBottom"),
  _sendButton: document.getElementById("send-button"),
  params: {
    _bubbleIcon: {
      src: "/static/images/panel-logo.png",
      className: "chat-bubble-icon",
      alt: "Chat bubble icon",
    },
    _iconAndContentContainer: { className: "icon-and-content" },
    _userMessageElement: { className: "message user" },
    _agentMessageElement: { className: "message agent" },
    _contentElement: { className: "message-content" },
    _loaderElement: {
      src: "/static/images/load-32_128.gif",
      className: "loader",
      alt: "lodding...",
    },
  },
};
