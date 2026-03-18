function toggleMenu(el) {
        const postId = el.dataset.id;
        const menu = document.getElementById("menu-" + postId);

        document.querySelectorAll(".post-menu").forEach((m) => {
          if (m !== menu) m.classList.remove("active");
        });

        menu.classList.toggle("active");
      }