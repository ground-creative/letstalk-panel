var APP = {
  debug: {
    log: function (msg, data = null) {
      if (APP.config.env != "dev") {
        return;
      }
      data ? console.log(msg, data) : console.log(msg);
    },
    error: function (msg, data = null) {
      if (APP.config.env != "dev") {
        return;
      }
      data ? console.error(msg, data) : console.log(msg);
    },
  },
  appendUserMessage: function (text) {
    const messageElement = document.createElement("div");
    Object.assign(messageElement, this.elements.params._userMessageElement);
    const contentElement = document.createElement("div");
    Object.assign(contentElement, this.elements.params._contentElement);
    contentElement.innerHTML = text
      .replace(/\n/g, "<br>")
      .replace(/\t/g, "&emsp;")
      .replace(/ /g, "&nbsp;");
    messageElement.appendChild(contentElement);
    this._appendMessageToChat(messageElement);
  },
  updateScrollStatus: function () {
    const chatWindow = APP.elements._chatWindow;
    APP._isAtBottom =
      chatWindow.scrollHeight - chatWindow.scrollTop <=
      chatWindow.clientHeight + 1;
    return APP._isAtBottom;
  },
  onScroll: function () {
    this._isAtBottom = APP.updateScrollStatus();
  },
  abortAppendMessage: function (typingInterval) {
    if (this._abortAppend) {
      clearInterval(typingInterval);
      this.updateSendButtonIcon(false);
      this.debug.log("Message append aborted!");
      return true;
    }
    return false;
  },
  appendAgentMessage: function (text) {
    this._abortAppend = false;
    const messageElement = document.createElement("div");
    Object.assign(messageElement, this.elements.params._agentMessageElement);
    const contentElement = document.createElement("div");
    Object.assign(contentElement, this.elements.params._contentElement);
    const bubbleIconElement = document.createElement("img");
    Object.assign(bubbleIconElement, this.elements.params._bubbleIcon);
    const iconAndContentContainer = document.createElement("div");
    Object.assign(
      iconAndContentContainer,
      this.elements.params._iconAndContentContainer
    );
    iconAndContentContainer.appendChild(bubbleIconElement);
    iconAndContentContainer.appendChild(contentElement);
    messageElement.appendChild(iconAndContentContainer);
    this.updateScrollStatus();
    this.elements._chatWindow.addEventListener(
      "scroll",
      this.updateScrollStatus
    );
    const formattedParts = this.formatter.formatMessage(text);
    let partIndex = 0;
    let index = 0;
    let totalLength = 0;
    formattedParts.forEach((part) => {
      if (part.type === "text") {
        totalLength += part.content.length;
      } else if (part.type === "code") {
        totalLength += 1;
      }
    });
    const typingInterval = setInterval(() => {
      if (this.abortAppendMessage(typingInterval)) {
        return;
      }

      if (partIndex < formattedParts.length) {
        if (this.abortAppendMessage(typingInterval)) {
          return;
        }

        const currentPart = formattedParts[partIndex];

        if (currentPart.type === "text") {
          if (index < currentPart.content.length) {
            if (this.abortAppendMessage(typingInterval)) {
              return;
            }
            const newChar = currentPart.content.charAt(index);
            contentElement.innerHTML += newChar === "\n" ? "<br>" : newChar;
            index++;
          } else {
            partIndex++;
            index = 0;
          }
        } else if (currentPart.type === "code") {
          if (index < currentPart.content.length) {
            if (this.abortAppendMessage(typingInterval)) {
              return;
            }
            let newChar = currentPart.content.charAt(index);
            if (index === 0) {
              const codeBlock = document.createElement("div");
              codeBlock.classList.add("code-block");
              const pre = document.createElement("pre");
              const code = document.createElement("code");
              codeBlock.appendChild(pre);
              pre.appendChild(code);
              contentElement.appendChild(codeBlock);
              currentPart.codeElement = code;
            }
            currentPart.codeElement.append(document.createTextNode(newChar));
            index++;
            if (index === currentPart.content.length) {
              const buttonHTML = `<button class="copy-button" onclick="APP.copyText(this)" data-clipboard-text="${APP.formatter.escapeHtml(
                currentPart.content
              )}"> 
                      <i class="fas fa-copy"></i>
                      <i class="fas fa-check copy-success" style="display: none;"></i>
                    </button>`;
              currentPart.codeElement.parentElement.innerHTML += buttonHTML;
            }
          } else {
            partIndex++;
            index = 0;
          }
        } else if (currentPart.type === "inlineCode") {
          if (index < currentPart.content.length) {
            if (this.abortAppendMessage(typingInterval)) {
              return;
            }
            const newChar = currentPart.content.charAt(index);
            if (index === 0) {
              const inlineCodeElement = document.createElement("span");
              inlineCodeElement.classList.add("inline-code");
              contentElement.appendChild(inlineCodeElement);
            }
            const inlineCodeElement = contentElement.lastChild;
            inlineCodeElement.append(document.createTextNode(newChar));
            index++;
          } else {
            partIndex++;
            index = 0;
          }
        }
      } else {
        clearInterval(typingInterval);
        this.updateSendButtonIcon(false);
      }

      if (APP._isAtBottom) {
        this.elements._chatWindow.scrollTop =
          this.elements._chatWindow.scrollHeight;
      }
    }, this.config.agent_typing_delay);

    setTimeout(() => {
      if (this._isAtBottom) {
        this.elements._chatWindow.scrollTop =
          this.elements._chatWindow.scrollHeight;
      }
      APP.elements._chatWindow.removeEventListener(
        "scroll",
        this.updateScrollStatus
      );
    }, (totalLength + 1) * this.config.agent_typing_delay);
    this._appendMessageToChat(messageElement);
  },
  copyText: function (button) {
    const text = button.getAttribute("data-clipboard-text");
    navigator.clipboard.writeText(text).then(() => {
      button.querySelector(".fa-copy").style.display = "none";
      button.querySelector(".fa-check").style.display = "inline";
      setTimeout(() => {
        button.querySelector(".fa-check").style.display = "none";
        button.querySelector(".fa-copy").style.display = "inline";
      }, 2000);
    });
  },
  updateSendButtonIcon: function (running = True) {
    if (running) {
      this.elements._sendButton.querySelector(
        ".fa-location-arrow"
      ).style.display = "none";
      this.elements._sendButton.querySelector(".fa-stop-circle").style.display =
        "flex";
    } else {
      this.elements._sendButton.querySelector(".fa-stop-circle").style.display =
        "none";
      this.elements._sendButton.querySelector(
        ".fa-location-arrow"
      ).style.display = "flex";
    }
  },
  sendMessage: async function () {
    APP.elements._messageInput.style.height = "auto";
    APP.elements._messageInput.style.height = `${APP.config.input_start_height}px`;
    if (this.abortController) {
      this.abortController.abort("Aborted by the user");
    }
    let aborted = false;
    this._abortAppend = true;
    this.abortController = new AbortController();
    const signal = this.abortController.signal;
    const message = this.elements._messageInput.value;
    if (!message.trim()) {
      this.updateSendButtonIcon(false);
      return;
    }
    this.updateSendButtonIcon(true);
    this.appendUserMessage(message);
    this.elements._messageInput.value = "";
    const loaderElement = this.showLoader();
    this.elements._chatWindow.scrollTo({
      top: this.elements._chatWindow.scrollHeight,
      behavior: "smooth",
    });
    try {
      const response = await this.services.completion(message, { signal });
      if (response.status === 200) {
        this.appendAgentMessage(response.message);
      } else if (response.status === 499) {
        aborted = true;
        this.debug.log("Message sending aborted by user", response);
        this.hideLoader(loaderElement);
        //this.abortController = null;
      } else {
        aborted = true;
        this.debug.log("Message sending returned error", response);
        this.hideLoader(loaderElement);
        //this.abortController = null;
      }
    } catch (error) {
      if (error.name === "AbortError") {
        this.debug.log("Message sending aborted");
      } else {
        this.debug.error("An error occurred:", error);
      }
    } finally {
      if (!aborted) {
        this.hideLoader(loaderElement);
        this.abortController = null;
      }
    }
  },
  showLoader: function () {
    const loaderElement = document.createElement("div");
    Object.assign(loaderElement, {
      className: this.elements.params._loaderElement.className,
      alt: this.elements.params._loaderElement.alt,
    });
    loaderElement.innerHTML = `<img src="${this.elements.params._loaderElement.src}" style="width: 35px; height: 35px;" alt="${this.elements.params._loaderElement.alt}">`;
    this.elements._chatWindow.appendChild(loaderElement);
    return loaderElement;
  },
  hideLoader: function (loaderElement) {
    this.elements._chatWindow.removeChild(loaderElement);
  },
  _isAtBottom: true,
  _abortAppend: false,
  _appendMessageToChat: function (messageElement) {
    this.elements._chatWindow.appendChild(messageElement);
    //this.elements._chatWindow.scrollTop =this.elements._chatWindow.scrollHeight;
  },
};
