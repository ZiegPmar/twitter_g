document.addEventListener('DOMContentLoaded', () => {
    // 1. Injection du CSS (Alignement strict + Scroll fix)
    const shareStyles = `
        .share-popup {
            display: none; position: fixed; z-index: 10000; left: 0; top: 0;
            width: 100%; height: 100%; background-color: rgba(0,0,0,0.85);
            align-items: center; justify-content: center; backdrop-filter: blur(5px);
        }
        .share-popup-content {
            background-color: #000; border: 1px solid #333; border-radius: 16px;
            width: 90%; max-width: 400px; max-height: 80vh; padding: 20px; color: white;
            box-shadow: 0 0 20px rgba(255,255,255,0.1); overflow-y: auto;
            display: flex; flex-direction: column;
        }
        .share-popup-header { 
            display: flex; justify-content: space-between; align-items: center; 
            margin-bottom: 15px; padding-bottom: 10px; border-bottom: 1px solid #222;
        }
        .share-popup-header h3 { margin: 0; font-size: 1.2rem; font-weight: 800; }
        .close-share-popup { background: none; border: none; color: #fff; font-size: 24px; cursor: pointer; }
        
        .share-popup-options { display: flex; flex-direction: column; gap: 4px; }
        
        /* ALIGNEMENT STRICT : L'icône a une place réservée fixe */
        .share-popup-item {
            display: flex; align-items: center; padding: 12px;
            border-radius: 10px; text-decoration: none; color: #fff;
            transition: background 0.2s;
        }
        .share-popup-item:hover { background-color: rgba(255,255,255,0.1); }
        
        .share-icon-wrapper {
            flex: 0 0 40px; /* Largeur fixe de 40px, ne bouge jamais */
            display: flex; justify-content: flex-start; align-items: center;
        }
        .share-popup-item i { font-size: 1.4rem; color: #fff !important; }
        .share-popup-item span { font-weight: 500; font-size: 1rem; }

        /* BOUTON COPIER : Placé à la fin du flux (s'affiche en bas du scroll) */
        .copy-link-btn { 
            margin-top: 20px; background-color: #fff !important; color: #000 !important; 
            justify-content: center; border-radius: 99px; border: none;
            padding: 14px; font-weight: 800; cursor: pointer; width: 100%;
            display: flex; align-items: center; gap: 10px;
        }
        .copy-link-btn i { color: #000 !important; }
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
                    <a href="#" id="share-x" target="_blank" class="share-popup-item"><div class="share-icon-wrapper"><i class="fa-brands fa-x-twitter" id="icon-x"></i></div> <span>X</span></a>
                    <a href="#" id="share-threads" target="_blank" class="share-popup-item"><div class="share-icon-wrapper"><i class="fa-brands fa-threads" id="icon-threads"></i></div> <span>Threads</span></a>
                    <a href="#" id="share-linkedin" target="_blank" class="share-popup-item"><div class="share-icon-wrapper"><i class="fa-brands fa-linkedin"></i></div> <span>LinkedIn</span></a>
                    <a href="#" id="share-facebook" target="_blank" class="share-popup-item"><div class="share-icon-wrapper"><i class="fa-brands fa-facebook"></i></div> <span>Facebook</span></a>
                    <a href="#" id="share-messenger" target="_blank" class="share-popup-item"><div class="share-icon-wrapper"><i class="fa-brands fa-facebook-messenger"></i></div> <span>Messenger</span></a>
                    <a href="#" id="share-whatsapp" target="_blank" class="share-popup-item"><div class="share-icon-wrapper"><i class="fa-brands fa-whatsapp"></i></div> <span>WhatsApp</span></a>
                    <a href="#" id="share-telegram" target="_blank" class="share-popup-item"><div class="share-icon-wrapper"><i class="fa-brands fa-telegram"></i></div> <span>Telegram</span></a>
                    <a href="#" id="share-discord" target="_blank" class="share-popup-item"><div class="share-icon-wrapper"><i class="fa-brands fa-discord"></i></div> <span>Discord</span></a>
                    <a href="#" id="share-reddit" target="_blank" class="share-popup-item"><div class="share-icon-wrapper"><i class="fa-brands fa-reddit"></i></div> <span>Reddit</span></a>
                    <a href="#" id="share-snapchat" target="_blank" class="share-popup-item"><div class="share-icon-wrapper"><i class="fa-brands fa-snapchat"></i></div> <span>Snapchat</span></a>
                    <a href="#" id="share-instagram" target="_blank" class="share-popup-item"><div class="share-icon-wrapper"><i class="fa-brands fa-instagram"></i></div> <span>Instagram</span></a>
                    <a href="#" id="share-tiktok" target="_blank" class="share-popup-item"><div class="share-icon-wrapper"><i class="fa-brands fa-tiktok"></i></div> <span>TikTok</span></a>
                    <a href="#" id="share-bereal" target="_blank" class="share-popup-item"><div class="share-icon-wrapper"><i class="fa-solid fa-camera-retro"></i></div> <span>BeReal</span></a>
                    <a href="#" id="share-pinterest" target="_blank" class="share-popup-item"><div class="share-icon-wrapper"><i class="fa-brands fa-pinterest"></i></div> <span>Pinterest</span></a>
                    <a href="#" id="share-tripadvisor" target="_blank" class="share-popup-item"><div class="share-icon-wrapper"><i class="fa-brands fa-tripadvisor" id="icon-tripadvisor"></i></div> <span>TripAdvisor</span></a>
                    <a href="#" id="share-booking" target="_blank" class="share-popup-item"><div class="share-icon-wrapper"><i class="fa-solid fa-hotel"></i></div> <span>Booking.com</span></a>
                    <a href="#" id="share-airbnb" target="_blank" class="share-popup-item"><div class="share-icon-wrapper"><i class="fa-brands fa-airbnb"></i></div> <span>Airbnb</span></a>
                    <a href="#" id="share-sncf" target="_blank" class="share-popup-item"><div class="share-icon-wrapper"><i class="fa-solid fa-train"></i></div> <span>SNCF Connect</span></a>
                    <a href="#" id="share-gmail" target="_blank" class="share-popup-item"><div class="share-icon-wrapper"><i class="fa-solid fa-envelope"></i></div> <span>Gmail</span></a>
                    <a href="#" id="share-github" target="_blank" class="share-popup-item"><div class="share-icon-wrapper"><i class="fa-brands fa-github"></i></div> <span>GitHub</span></a>
                    <a href="#" id="share-skribbl" target="_blank" class="share-popup-item"><div class="share-icon-wrapper"><i class="fa-solid fa-pen-nib"></i></div> <span>Skribbl.io</span></a>
                    <a href="#" id="share-cemantix" target="_blank" class="share-popup-item"><div class="share-icon-wrapper"><i class="fa-solid fa-fire-flame-curved"></i></div> <span>Cémantix</span></a>
                    <a href="#" id="share-pedantix" target="_blank" class="share-popup-item"><div class="share-icon-wrapper"><i class="fa-solid fa-book-open"></i></div> <span>Pédantix</span></a>
                    <a href="#" id="share-myme" target="_blank" class="share-popup-item"><div class="share-icon-wrapper"><i class="fa-solid fa-shoe-prints"></i></div> <span>MYM</span></a>
                    <a href="#" id="share-onlyfans" target="_blank" class="share-popup-item"><div class="share-icon-wrapper"><i class="fa-solid fa-star"></i></div> <span>OnlyFans</span></a>
                    <a href="#" id="share-wikifeet" target="_blank" class="share-popup-item"><div class="share-icon-wrapper"><i class="fa-solid fa-socks"></i></div> <span>WikiFeet</span></a>
                    <a href="#" id="share-pornhub" target="_blank" class="share-popup-item"><div class="share-icon-wrapper"><i class="fa-solid fa-circle-play"></i></div> <span>Pornhub</span></a>
                    <a href="#" id="share-xnxx" target="_blank" class="share-popup-item"><div class="share-icon-wrapper"><i class="fa-solid fa-film"></i></div> <span>XNXX</span></a>
                    <a href="#" id="share-tukif" target="_blank" class="share-popup-item"><div class="share-icon-wrapper"><i class="fa-solid fa-heart"></i></div> <span>Tukif</span></a>

                    <button id="share-popup-copy-btn" class="copy-link-btn">
                        <i class="fa-solid fa-link"></i> <span id="share-popup-copy-text">Copier le lien</span>
                    </button>
                </div>
            </div>
        </div>
    `;
    document.body.insertAdjacentHTML('beforeend', shareModalHTML);

    const modal = document.getElementById('share-popup-modal');
    const copyText = document.getElementById('share-popup-copy-text');
    let currentUrlToShare = "";

    // 3. Fallback pour icônes manquantes
    const checkIcons = () => {
        const fallbacks = [
            { id: 'icon-x', class: 'fa-brands fa-twitter' },
            { id: 'icon-threads', class: 'fa-solid fa-at' },
            { id: 'icon-tripadvisor', class: 'fa-solid fa-compass' }
        ];
        fallbacks.forEach(item => {
            const icon = document.getElementById(item.id);
            if (icon && icon.offsetWidth === 0) icon.className = item.class;
        });
    };

    const closeShareModal = () => { modal.style.display = 'none'; copyText.innerText = "Copier le lien"; };
    document.getElementById('close-share-popup-btn').addEventListener('click', closeShareModal);
    modal.addEventListener('click', (e) => { if (e.target === modal) closeShareModal(); });

    document.getElementById('share-popup-copy-btn').addEventListener('click', async () => {
        try {
            await navigator.clipboard.writeText(currentUrlToShare);
            copyText.innerText = "Copié !";
            setTimeout(closeShareModal, 1000);
        } catch (err) { console.error(err); }
    });

    document.addEventListener('click', (e) => {
        const shareBtn = e.target.closest('.js-share-btn');
        if (shareBtn) {
            e.preventDefault();
            const postArticle = shareBtn.closest('.post');
            const postLink = postArticle?.querySelector('.post-content-link');
            currentUrlToShare = postLink ? window.location.origin + postLink.getAttribute('href') : window.location.href;

            const encUrl = encodeURIComponent(currentUrlToShare);
            const encTxt = encodeURIComponent("Regarde ça : ");

            document.getElementById('share-x').href = `https://twitter.com/intent/tweet?url=${encUrl}&text=${encTxt}`;
            document.getElementById('share-threads').href = `https://www.threads.net/intent/post?text=${encTxt}${encUrl}`;
            document.getElementById('share-linkedin').href = `https://www.linkedin.com/sharing/share-offsite/?url=${encUrl}`;
            document.getElementById('share-facebook').href = `https://www.facebook.com/sharer/sharer.php?u=${encUrl}`;
            document.getElementById('share-whatsapp').href = `https://api.whatsapp.com/send?text=${encTxt}${encUrl}`;
            document.getElementById('share-telegram').href = `https://t.me/share/url?url=${encUrl}&text=${encTxt}`;
            document.getElementById('share-reddit').href = `https://reddit.com/submit?url=${encUrl}&title=${encTxt}`;
            document.getElementById('share-pinterest').href = `https://pinterest.com/pin/create/button/?url=${encUrl}`;
            document.getElementById('share-gmail').href = `https://mail.google.com/mail/?view=cm&fs=1&tf=1&to=&su=Lien&body=${encUrl}`;
            
            const apps = ['messenger', 'instagram', 'tiktok', 'snapchat', 'discord', 'bereal', 'tripadvisor', 'booking', 'airbnb', 'sncf', 'skribbl', 'cemantix', 'pedantix', 'wikifeet', 'myme', 'onlyfans', 'pornhub', 'xnxx', 'tukif', 'github'];
            const urls = ["fb-messenger://share/?link=", "https://instagram.com/", "https://tiktok.com/", "https://snapchat.com/", "https://discord.com/", "https://bereal.com/", "https://tripadvisor.fr/", "https://booking.com/", "https://airbnb.fr/", "https://sncf-connect.com/", "https://skribbl.io/", "https://cemantix.certitudes.org/", "https://cemantix.certitudes.org/pedantix", "https://wikifeet.com/", "https://mym.fans/", "https://onlyfans.com/", "https://pornhub.com/", "https://xnxx.com/", "https://tukif.com/", "https://github.com/"];
            
            apps.forEach((id, i) => {
                const el = document.getElementById(`share-${id}`);
                if (el) el.href = urls[i] + (id === 'messenger' ? encUrl : '');
            });

            modal.style.display = 'flex';
            checkIcons();
        }
    });
});