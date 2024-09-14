APP.formatter = {
  escapeHtml: function (text) {
    return text
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;")
      .replace(/'/g, "&#039;");
  },
  formatMessage: function (text) {
    const codeBlockPattern = /```([\s\S]*?)```/g;
    const inlineCodePattern = /`([^`]+)`/g;
    let parts = [];
    let lastIndex = 0;

    // Combine code block and inline code processing
    const combinedPattern = new RegExp(
      `${codeBlockPattern.source}|${inlineCodePattern.source}`,
      "g"
    );

    text.replace(combinedPattern, (match, codeBlockCode, inlineCode, index) => {
      if (lastIndex < index) {
        parts.push({ type: "text", content: text.slice(lastIndex, index) });
      }

      if (codeBlockCode) {
        parts.push({ type: "code", content: codeBlockCode });
      } else if (inlineCode) {
        parts.push({ type: "inlineCode", content: inlineCode });
      }

      lastIndex = index + match.length;
    });

    // Capture any remaining text
    if (lastIndex < text.length) {
      parts.push({ type: "text", content: text.slice(lastIndex) });
    }

    APP.debug.log("parts", parts);
    return parts;
  },
};
