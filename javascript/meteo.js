async function chargerMeteo() {
    const monLienAPI = "https://api.open-meteo.com/v1/forecast?latitude=45.7485&longitude=4.8467&current_weather=true";

    try {
        const reponse = await fetch(monLienAPI);
        const donnees = await reponse.json();

        if (donnees.current_weather) {
            const temperature = donnees.current_weather.temperature;
            const vent = donnees.current_weather.windspeed;

            // On remplit les éléments du widget
            document.getElementById('temp-affichage').innerText = temperature;
            document.getElementById('vent-affichage').innerText = vent + " km/h";
            
            // Bonus : Met à jour la date
            const options = { weekday: 'long', day: 'numeric', month: 'long' };
            document.getElementById('current-date').innerText = new Date().toLocaleDateString('fr-FR', options);
        }
    } catch (erreur) {
        console.error("Erreur :", erreur);
        document.getElementById('vent-affichage').innerText = "Erreur de connexion";
    }
}

chargerMeteo();