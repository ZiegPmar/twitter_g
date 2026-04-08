document.addEventListener('DOMContentLoaded', () => {
    // 1. Injection du CSS (Design Dark Mode)
    const shareStyles = `
        .share-popup {
            display: none; position: fixed; z-index: 10000; left: 0; top: 0;
            width: 100%; height: 100%; background-color: rgba(0,0,0,0.85);
            align-items: center; justify-content: center; backdrop-filter: blur(5px);
        }
        .share-popup-content {
            background-color: #000; border: 1px solid #333; border-radius: 16px;
            width: 90%; max-width: 350px; padding: 24px; color: white;
            box-shadow: 0 0 20px rgba(255,255,255,0.1);
        }
        .share-popup-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px; }
        .share-popup-header h3 { margin: 0; font-size: 1.25rem; font-weight: 800; color: #fff; }
        .close-share-popup { background: none; border: none; color: #fff; font-size: 22px; cursor: pointer; padding: 5px; }
        .share-popup-options { display: flex; flex-direction: column; gap: 5px; }
        .share-popup-item {
            display: flex; align-items: center; gap: 20px; padding: 12px;
            border-radius: 8px; text-decoration: none; color: #fff;
            font-weight: 600; font-size: 1rem; transition: background 0.2s;
        }
        .share-popup-item:hover { background-color: rgba(255,255,255,0.1); }
        .share-popup-item i { width: 30px; text-align: center; font-size: 1.4rem; color: #fff !important; }
        .copy-link-btn { 
            margin-top: 15px; background-color: #fff !important; color: #000 !important; 
            justify-content: center; border-radius: 99px; border: none;
            padding: 12px; font-weight: 800; cursor: pointer; width: 100%;
        }
        .copy-link-btn:hover { background-color: #e6e6e6 !important; }
        .copy-link-btn i { color: #000 !important; font-size: 1.2rem; }
    `;
    const styleSheet = document.createElement("style");
    styleSheet.innerText = shareStyles;
    document.head.appendChild(styleSheet);

    // 2. Injection du HTML
    const shareModalHTML = `
        <div id="share-popup-modal" class="share-popup">
            <div class="share-popup-content">
                <div class="share-popup-header">
                    <h3>Partager</h3>
                    <button class="close-share-popup" id="close-share-popup-btn"><i class="fa-solid fa-xmark"></i></button>
                </div>
                <div class="share-popup-options">
                    <a href="#" id="share-popup-x" target="_blank" class="share-popup-item">
                        <i class="fa-brands fa-x-twitter" id="icon-x"></i> <span>Partager sur X</span>
                    </a>
                    <a href="#" id="share-popup-whatsapp" target="_blank" class="share-popup-item">
                        <i class="fa-brands fa-whatsapp"></i> <span>WhatsApp</span>
                    </a>
                    <a href="#" id="share-popup-facebook" target="_blank" class="share-popup-item">
                        <i class="fa-brands fa-facebook"></i> <span>Facebook</span>
                    </a>
                    <button id="share-popup-copy-btn" class="share-popup-item copy-link-btn">
                        <i class="fa-solid fa-link"></i> <span id="share-popup-copy-text">Copier le lien</span>
                    </button>
                </div>
            </div>
        </div>
    `;
    document.body.insertAdjacentHTML('beforeend', shareModalHTML);

    let currentUrlToShare = "";
    const modal = document.getElementById('share-popup-modal');
    const copyText = document.getElementById('share-popup-copy-text');

    // Vérification de l'icône X (Sécurité)
    setTimeout(() => {
        const xIcon = document.getElementById('icon-x');
        if (xIcon && xIcon.offsetWidth === 0) {
            // Si l'icône ne s'affiche pas, on tente l'ancien logo Twitter
            xIcon.className = "fa-brands fa-twitter";
        }
    }, 500);

    const closeShareModal = () => { 
        modal.style.display = 'none'; 
        copyText.innerText = "Copier le lien";
    };

    document.getElementById('close-share-popup-btn').addEventListener('click', closeShareModal);
    modal.addEventListener('click', (e) => { if (e.target === modal) closeShareModal(); });

    document.getElementById('share-popup-copy-btn').addEventListener('click', async () => {
        try {
            await navigator.clipboard.writeText(currentUrlToShare);
            copyText.innerText = "Copié !";
            setTimeout(closeShareModal, 1000);
        } catch (err) {
            console.error("Erreur de copie", err);
        }
    });

    document.addEventListener('click', (e) => {
        const shareBtn = e.target.closest('.js-share-btn');
        if (shareBtn) {
            e.preventDefault();
            const postArticle = shareBtn.closest('.post');
            const postLink = postArticle?.querySelector('.post-content-link');
            
            currentUrlToShare = postLink 
                ? window.location.origin + postLink.getAttribute('href') 
                : window.location.href;

            const shareText = encodeURIComponent("Regarde ce post ! ");
            const encodedUrl = encodeURIComponent(currentUrlToShare);

            document.getElementById('share-popup-x').href = `https://twitter.com/intent/tweet?text=${shareText}&url=${encodedUrl}`;
            document.getElementById('share-popup-whatsapp').href = `https://api.whatsapp.com/send?text=${shareText}${encodedUrl}`;
            document.getElementById('share-popup-facebook').href = `https://www.facebook.com/sharer/sharer.php?u=${encodedUrl}`;

            modal.style.display = 'flex';
        }
    });
});