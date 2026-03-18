      const mediaModal = document.getElementById("mediaModal");
      const openMediaModal = document.getElementById("openMediaModal");
      const closeMediaModal = document.getElementById("closeMediaModal");
      const cancelMediaModal = document.getElementById("cancelMediaModal");
      const saveMediaModal = document.getElementById("saveMediaModal");

      const mediaUrlField = document.getElementById("mediaUrlField");
      const mediaUrlInput = document.getElementById("mediaUrlInput");

      const mediaPreviewBox = document.getElementById("mediaPreviewBox");
      const mediaPreviewImg = document.getElementById("mediaPreviewImg");
      const removeMediaBtn = document.getElementById("removeMediaBtn");

      function openModal() {
        mediaModal.style.display = "flex";
        mediaUrlField.value = mediaUrlInput.value;
        mediaUrlField.focus();
      }

      function closeModal() {
        mediaModal.style.display = "none";
      }

      function updatePreview() {
        const url = mediaUrlInput.value.trim();

        if (!url) {
          mediaPreviewBox.style.display = "none";
          mediaPreviewImg.src = "";
          return;
        }

        mediaPreviewImg.src = url;
        mediaPreviewBox.style.display = "block";
      }

      openMediaModal.addEventListener("click", openModal);
      closeMediaModal.addEventListener("click", closeModal);
      cancelMediaModal.addEventListener("click", closeModal);

      saveMediaModal.addEventListener("click", () => {
        mediaUrlInput.value = mediaUrlField.value.trim();
        updatePreview();
        closeModal();
      });

      removeMediaBtn.addEventListener("click", () => {
        mediaUrlInput.value = "";
        mediaUrlField.value = "";
        updatePreview();
      });

      mediaModal.addEventListener("click", (e) => {
        if (e.target === mediaModal) {
          closeModal();
        }
      });

      updatePreview();