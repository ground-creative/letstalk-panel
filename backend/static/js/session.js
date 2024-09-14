APP.session = {
  getBaseUrl: function (url) {
    const urlObject = new URL(url);
    return urlObject.origin + urlObject.pathname;
  },
  getSessionIdForUrl: function (url) {
    const baseUrl = this.getBaseUrl(url);
    let sessionId = localStorage.getItem(baseUrl);

    if (!sessionId) {
      sessionId = this.generateSessionId();
      localStorage.setItem(baseUrl, sessionId);
    }

    return sessionId;
  },
  generateSessionId: function () {
    return "_" + Math.random().toString(36).substr(2, 9);
  },
  sessionId: null,
};
