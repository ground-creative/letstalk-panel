// Add event listener for Enter key press
APP.elements._messageInput.addEventListener("keydown", function (event) {
  if (event.key === "Enter") {
    if (event.shiftKey) {
      //APP.elements._messageInput.value += "\n";
    } else {
      event.preventDefault();
      APP.sendMessage();
    }
  }
});

document.addEventListener("DOMContentLoaded", () => {
  const updateScrollStatus = () => {
    const chatWindow = APP.elements._chatWindow;
    const isAtBottom =
      chatWindow.scrollHeight - chatWindow.scrollTop <=
      chatWindow.clientHeight + 1;
    APP.elements._scrollToBottom.style.display = isAtBottom ? "none" : "flex";
  };

  APP.elements._chatWindow.addEventListener("scroll", updateScrollStatus);

  // Function to handle the scroll-to-bottom button click
  const handleScrollToBottomClick = () => {
    const chatWindow = APP.elements._chatWindow;
    chatWindow.scrollTo({
      top: chatWindow.scrollHeight,
      behavior: "smooth",
    });
  };

  // Add a scroll event listener to update the scroll status
  APP.elements._chatWindow.addEventListener("scroll", updateScrollStatus);

  // Add click event listener for the scroll-to-bottom button
  APP.elements._scrollToBottom.addEventListener(
    "click",
    handleScrollToBottomClick
  );

  APP.session.sessionId = APP.session.getSessionIdForUrl(window.location.href);
  APP.debug.log("Session ID for this URL:", APP.sessionId);

  if (APP.start_message) {
    APP.appendAgentMessage(APP.start_message);
  }
});

window.addEventListener("resize", function () {
  const chatWindow = APP.elements._chatWindow;
  const hasScrollbar = chatWindow.scrollHeight > chatWindow.clientHeight;
  APP.debug.log("hasScrollbar", hasScrollbar);
  if (!hasScrollbar) {
    APP.elements._scrollToBottom.style.display = "none";
  } else {
    const isAtBottom =
      chatWindow.scrollHeight - chatWindow.scrollTop <=
      chatWindow.clientHeight + 1;
    APP.elements._scrollToBottom.style.display = isAtBottom ? "none" : "flex";
  }
});

APP.elements._messageInput.addEventListener("input", function () {
  if (this.scrollHeight < 62) {
    this.style.height = "auto"; // Reset height
    this.style.height = `${APP.config.input_start_height}px`; // Set to scroll height
    return;
  }
  this.style.height = "auto"; // Reset height
  this.style.height = `${this.scrollHeight}px`; // Set to scroll height
});
