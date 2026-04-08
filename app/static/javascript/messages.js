document.addEventListener("DOMContentLoaded", () => {
  const csrfToken = document
    .querySelector('meta[name="csrf-token"]')
    ?.getAttribute("content");

  const pageData = document.getElementById("messages-page-data");

  const toggleNewMessageBtn = document.getElementById("toggle-new-message");
  const newMessagePanel = document.getElementById("new-message-panel");
  const userSearchInput = document.getElementById("user-search");
  const userResults = document.getElementById("user-results");

  const conversationButtons = document.querySelectorAll(".conversation-item");

  const emptyConversation = document.getElementById("empty-conversation");
  const conversationView = document.getElementById("conversation-view");
  const conversationHeader = document.getElementById("conversation-header");
  const messagesThread = document.getElementById("messages-thread");
  const messageForm = document.getElementById("message-form");
  const messageInput = document.getElementById("message-input");

  let activeUserId = null;
  let activeUserData = null;

  function escapeHtml(text) {
    const div = document.createElement("div");
    div.textContent = text ?? "";
    return div.innerHTML;
  }

  function getAvatarUrl(avatar) {
    if (avatar && avatar.trim() !== "") {
      return `/static/img/Avatar/${avatar}`;
    }

    return `/static/img/Avatar/47fef09b5e072de28b79f35d0ef4e9cc.webp`;
  }

  function formatMessageDate(dateString) {
    if (!dateString) return "";

    const date = new Date(dateString);
    if (Number.isNaN(date.getTime())) return dateString;

    return date.toLocaleString("fr-FR", {
      day: "2-digit",
      month: "2-digit",
      hour: "2-digit",
      minute: "2-digit"
    });
  }

  function setActiveConversationButton(userId) {
    document.querySelectorAll(".conversation-item").forEach((item) => {
      const itemUserId = Number(item.dataset.userId);

      if (itemUserId === Number(userId)) {
        item.classList.add("active");
      } else {
        item.classList.remove("active");
      }
    });
  }

  function showConversationView() {
    emptyConversation.classList.add("hidden");
    conversationView.classList.remove("hidden");
  }

  function showErrorMessage(message) {
    messagesThread.innerHTML = `
      <div class="no-messages">${escapeHtml(message)}</div>
    `;
  }

  function renderConversationHeader(user) {
    conversationHeader.innerHTML = `
      <img
        src="${escapeHtml(getAvatarUrl(user.avatar_url || ""))}"
        alt="Avatar"
        class="conversation-header-avatar" />

      <div class="conversation-header-text">
        <h2>${escapeHtml(user.display_name || "Utilisateur")}</h2>
        <p>@${escapeHtml(user.username || "")}</p>
      </div>
    `;
  }

  function renderMessages(messages) {
    messagesThread.innerHTML = "";

    if (!messages.length) {
      messagesThread.innerHTML = `
        <div class="no-messages">
          Aucun message pour le moment. Envoie le premier.
        </div>
      `;
      return;
    }

    messages.forEach((msg) => {
      const row = document.createElement("div");
      row.className = "message-row";

      if (Number(msg.sender_id) === Number(activeUserId)) {
        row.classList.add("them");
      } else {
        row.classList.add("me");
      }

      row.innerHTML = `
        <div class="message-bubble">
          <p>${escapeHtml(msg.content || "")}</p>
          <span class="message-time">${escapeHtml(formatMessageDate(msg.created_at))}</span>
        </div>
      `;

      messagesThread.appendChild(row);
    });

    messagesThread.scrollTop = messagesThread.scrollHeight;
  }

  async function markAsRead(userId) {
    try {
      const response = await fetch(`/api/messages/read/${userId}`, {
        method: "POST",
        headers: {
          "X-CSRFToken": csrfToken
        }
      });

      const data = await response.json().catch(() => ({}));

      if (!response.ok) {
        console.error("Erreur markAsRead :", data);
      }
    } catch (error) {
      console.error("Erreur lors du marquage comme lu :", error);
    }
  }

  async function loadMessages(user) {
    activeUserId = Number(user.id || user.other_user_id);
    activeUserData = {
      id: activeUserId,
      username: user.username,
      display_name: user.display_name,
      avatar_url: user.avatar_url || ""
    };

    showConversationView();
    renderConversationHeader(activeUserData);
    setActiveConversationButton(activeUserId);

    try {
      const response = await fetch(`/api/messages/${activeUserId}`);
      const data = await response.json();

      if (!response.ok) {
        showErrorMessage(data.error || "Impossible de charger les messages.");
        return;
      }

      const messages = Array.isArray(data.messages) ? data.messages : [];
      renderMessages(messages);

      await markAsRead(activeUserId);
    } catch (error) {
      console.error("Erreur chargement messages :", error);
      showErrorMessage("Impossible de charger les messages.");
    }
  }

  async function sendMessage() {
    if (!activeUserId) return;

    const content = messageInput.value.trim();
    if (!content) return;

    try {
      const response = await fetch(`/api/messages/send/${activeUserId}`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "X-CSRFToken": csrfToken
        },
        body: JSON.stringify({ content })
      });

      const data = await response.json().catch(() => ({}));
      console.log("Réponse send:", data);

      if (!response.ok) {
        alert(data.error || "Erreur lors de l'envoi du message.");
        return;
      }

      messageInput.value = "";
      await loadMessages(activeUserData);
    } catch (error) {
      console.error("Erreur envoi message :", error);
      alert("Erreur technique lors de l'envoi.");
    }
  }

  toggleNewMessageBtn?.addEventListener("click", () => {
    newMessagePanel.classList.toggle("hidden");

    if (!newMessagePanel.classList.contains("hidden")) {
      userSearchInput.focus();
    }
  });

  userSearchInput?.addEventListener("input", async () => {
    const query = userSearchInput.value.trim();

    if (!query) {
      userResults.innerHTML = "";
      return;
    }

    try {
      const response = await fetch(
        `/api/users/search?q=${encodeURIComponent(query)}`
      );
      const data = await response.json();

      const users = Array.isArray(data.users) ? data.users : [];
      userResults.innerHTML = "";

      if (!users.length) {
        userResults.innerHTML = `
          <div class="user-result-empty">Aucun compte suivi trouvé.</div>
        `;
        return;
      }

      users.forEach((user) => {
        const item = document.createElement("button");
        item.type = "button";
        item.className = "user-result";

        item.innerHTML = `
          <img
            src="${escapeHtml(getAvatarUrl(user.avatar_url || ""))}"
            alt="Avatar"
            class="user-result-avatar" />

          <div class="user-result-text">
            <strong>${escapeHtml(user.display_name)}</strong>
            <span>@${escapeHtml(user.username)}</span>
          </div>
        `;

        item.addEventListener("click", async () => {
          history.replaceState(null, "", `/messages?user_id=${user.id}`);
          newMessagePanel.classList.add("hidden");
          userSearchInput.value = "";
          userResults.innerHTML = "";

          await loadMessages(user);
        });

        userResults.appendChild(item);
      });
    } catch (error) {
      console.error("Erreur recherche utilisateurs :", error);
      userResults.innerHTML = `
        <div class="user-result-empty">Erreur lors de la recherche.</div>
      `;
    }
  });

  conversationButtons.forEach((button) => {
    button.addEventListener("click", async () => {
      const user = {
        other_user_id: button.dataset.userId,
        username: button.dataset.username,
        display_name: button.dataset.displayName,
        avatar_url: button.dataset.avatar
      };

      history.replaceState(null, "", `/messages?user_id=${button.dataset.userId}`);
      await loadMessages(user);
    });
  });

  messageForm?.addEventListener("submit", async (e) => {
    e.preventDefault();
    await sendMessage();
  });

  messageInput?.addEventListener("keydown", async (e) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      await sendMessage();
    }
  });

  if (pageData) {
    const selectedUserId = pageData.dataset.selectedUserId;
    const selectedUsername = pageData.dataset.selectedUsername;
    const selectedDisplayName = pageData.dataset.selectedDisplayName;
    const selectedAvatar = pageData.dataset.selectedAvatar;

    if (selectedUserId) {
      loadMessages({
        id: selectedUserId,
        username: selectedUsername,
        display_name: selectedDisplayName,
        avatar_url: selectedAvatar
      });
    }
  }
});