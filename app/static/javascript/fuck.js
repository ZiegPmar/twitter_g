document.addEventListener('DOMContentLoaded', () => {
    // 1. Tes deux images
    const imageInitiale = "/static/img/Guardia_Strip.png";
    const imageSuivante = "/static/img/singe.jpg";
    
    const imgElement = document.getElementById('sidebar-img');
    const closeBtn = document.getElementById('close-image');
    const container = document.getElementById('image-container');

    if(closeBtn && imgElement) {
        closeBtn.addEventListener('click', (e) => {
            // Empêche d'autres actions
            e.preventDefault();
            e.stopPropagation();

            // 2. On change la source de l'image
            imgElement.src = imageSuivante;

            // 3. On cache la croix pour qu'on ne puisse plus cliquer dessus
            closeBtn.style.display = 'none';

            // Optionnel : Si tu veux aussi empêcher le clic sur l'image après
            imgElement.style.pointerEvents = 'none';
            imgElement.style.cursor = 'default';
        });
    }
});