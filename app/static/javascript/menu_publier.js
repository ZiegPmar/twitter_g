document.addEventListener('DOMContentLoaded', () => {

    const publishModal = document.getElementById('publishModalOverlay');
    const openBtn = document.getElementById('openPublishModalBtn');
    const closeBtn = document.getElementById('closePublishModalBtn');
    const modalAddMediaBtn = document.getElementById('modalAddMediaBtn');
    const modalMediaInput = document.getElementById('modalMediaInput');
    const modalGifBtn = document.getElementById('modalGifBtn');
    const modalImgPreviewContainer = document.getElementById('modalImgPreviewContainer');
    const modalImgPreview = document.getElementById('modalImgPreview');
    const modalRemoveImgBtn = document.getElementById('modalRemoveImgBtn');
    const modalEmojiBtn = document.getElementById('modalEmojiBtn');
    const emojiPickerContainer = document.getElementById('emojiPickerContainer');
    const modalTextarea = document.getElementById('modalTextarea');

    // 1. GESTION DE LA MODAL (OUVRIR / FERMER)
    if (openBtn) {
        openBtn.addEventListener('click', () => {
            publishModal.style.display = 'flex';
        });
    }

    if (closeBtn) {
        closeBtn.addEventListener('click', () => {
            publishModal.style.display = 'none';
            emojiPickerContainer.style.display = 'none'; 
        });
    }

    // 2. GESTION DE L'IMAGE (UPLOAD LOCAL)
    if (modalAddMediaBtn && modalMediaInput) {
        modalAddMediaBtn.addEventListener('click', () => {
            modalMediaInput.click(); 
        });

        modalMediaInput.addEventListener('change', function() {
            const file = this.files[0];
            if (file) {
                const reader = new FileReader();
                reader.onload = function(e) {
                    modalImgPreview.src = e.target.result;
                    modalImgPreviewContainer.style.display = 'block';
                }
                reader.readAsDataURL(file);
            }
        });
    }

    // 3. GESTION DU GIF (PROMPT URL)
    if (modalGifBtn) {
        modalGifBtn.addEventListener('click', () => {
            const url = prompt("Collez le lien de votre GIF (Tenor, Giphy, etc) :");
            if (url && url.trim() !== "") {
                if(modalMediaInput) modalMediaInput.value = ""; 
                modalImgPreview.src = url.trim();
                modalImgPreviewContainer.style.display = 'block';
            }
        });
    }

    // 4. SUPPRIMER LE MÉDIA (IMAGE OU GIF)
    if (modalRemoveImgBtn) {
        modalRemoveImgBtn.addEventListener('click', () => {
            if(modalMediaInput) modalMediaInput.value = ""; 
            modalImgPreview.src = "";
            modalImgPreviewContainer.style.display = 'none';
        });
    }

    // 5. EMOJIMART
    if (window.EmojiMart) {
        if (emojiPickerContainer && emojiPickerContainer.innerHTML === "") {
            const pickerOptions = {
                theme: 'dark',
                locale: 'fr',
                onEmojiSelect: (emoji) => {
                    modalTextarea.value += emoji.native;
                    modalTextarea.focus();
                }
            };
            const picker = new EmojiMart.Picker(pickerOptions);
            emojiPickerContainer.appendChild(picker);
        }
    } else {
        console.error("Erreur: EmojiMart n'est pas chargé via CDN.");
    }

    if (modalEmojiBtn) {
        modalEmojiBtn.addEventListener('click', (e) => {
            e.preventDefault();
            e.stopPropagation(); 
            const isHidden = (emojiPickerContainer.style.display === 'none' || emojiPickerContainer.style.display === '');
            emojiPickerContainer.style.display = isHidden ? 'block' : 'none';
        });
    }

    // 6. FERMETURE AU CLIC EXTÉRIEUR
    window.addEventListener('click', (e) => {
        if (emojiPickerContainer && emojiPickerContainer.style.display === 'block') {
            if (!emojiPickerContainer.contains(e.target) && !modalEmojiBtn.contains(e.target)) {
                emojiPickerContainer.style.display = 'none';
            }
        }
        
        if (e.target === publishModal) {
            publishModal.style.display = 'none';
            if(emojiPickerContainer) emojiPickerContainer.style.display = 'none';
        }
    });
});