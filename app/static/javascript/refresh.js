const pullRefresh = document.getElementById("pullRefreshBottom");
      const pullRefreshText = document.getElementById("pullRefreshBottomText");
      const layout = document.querySelector(".layout");

      let startY = 0;
      let currentPull = 0;
      let isPulling = false;
      let isRefreshing = false;

      const triggerPull = 80;
      const maxPull = 120;

      function isAtBottom() {
        return (
          window.scrollY + window.innerHeight >=
          document.documentElement.scrollHeight - 5
        );
      }

      function setPull(distance) {
        const clamped = Math.min(distance, maxPull);
        currentPull = clamped;

        pullRefresh.style.transition = "none";
        pullRefresh.style.height = clamped + "px";

        layout.style.transition = "none";
        layout.style.marginBottom = clamped + "px";

        if (clamped > 10) {
          pullRefresh.classList.add("visible");
        } else {
          pullRefresh.classList.remove("visible");
        }

        pullRefreshText.textContent =
          clamped >= triggerPull
            ? "Relâche pour rafraîchir"
            : "Tire pour rafraîchir";
      }

      function resetPull() {
        pullRefresh.style.transition = "height 0.3s ease";
        pullRefresh.style.height = "0px";

        layout.style.transition = "margin-bottom 0.3s ease";
        layout.style.marginBottom = "0px";

        pullRefresh.classList.remove("visible", "refreshing");
        pullRefreshText.textContent = "Tire pour rafraîchir";
        currentPull = 0;
        isPulling = false;
      }

      function triggerRefresh() {
        isRefreshing = true;

        pullRefresh.style.transition = "height 0.2s ease";
        pullRefresh.style.height = "70px";

        layout.style.transition = "margin-bottom 0.2s ease";
        layout.style.marginBottom = "70px";

        pullRefresh.classList.add("visible", "refreshing");
        pullRefreshText.textContent = "Rafraîchissement...";

        setTimeout(() => {
          window.scrollTo({ top: 0, behavior: "smooth" });
          setTimeout(() => {
            resetPull();
            isRefreshing = false;
          }, 600);
        }, 800);
      }

      /* Touch */
      window.addEventListener("touchstart", (e) => {
        if (isAtBottom() && !isRefreshing) {
          startY = e.touches[0].clientY;
          isPulling = true;
        }
      });

      window.addEventListener(
        "touchmove",
        (e) => {
          if (!isPulling || isRefreshing) return;
          const diff = startY - e.touches[0].clientY;
          if (diff > 0) {
            e.preventDefault();
            setPull(diff * 0.6);
          }
        },
        { passive: false },
      );

      window.addEventListener("touchend", () => {
        if (!isPulling || isRefreshing) return;
        currentPull >= triggerPull ? triggerRefresh() : resetPull();
      });

      /* Souris — wheel event pour desktop */
      window.addEventListener("wheel", (e) => {
        if (!isAtBottom() || isRefreshing) return;

        if (e.deltaY > 0) {
          currentPull = Math.min(currentPull + e.deltaY * 0.4, maxPull);
          setPull(currentPull);

          clearTimeout(window._pullResetTimer);
          window._pullResetTimer = setTimeout(() => {
            if (!isRefreshing) {
              if (currentPull >= triggerPull) {
                triggerRefresh();
              } else {
                resetPull();
              }
            }
          }, 300);
        }
      });