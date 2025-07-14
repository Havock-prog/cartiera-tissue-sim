import numpy as np

class Bobina:
    """
    Crea una nuova bobina da formare da 0
    """
    def __init__(self, grammatura_target, sigma, indice_qualita, lunghezza_max=50000):
        self.lunghezza = 0
        self.peso_bobina = 0
        self.delta_peso_bobina = 0 #peso prodotto in un tick
        self.sigma = sigma
        self.grammatura_target = grammatura_target
        self.grammatura = np.random.normal(self.grammatura_target, self.sigma)
        self.lunghezza_max = lunghezza_max
        self.completata = False
        self.indice_qualita = indice_qualita
        

    def aggiorna_peso(self, tick_duration, velocita_tela, larghezza=2.75):
        """
        Aggiorna peso bobina di un tick di simulazione (5 sec)
        """
        # velocità pope: si considera che la velocità effettiva sia l'85% della velocità tela
        velocita_pope = velocita_tela * 0.85
        # Lunghezza prodotta nel tick
        delta_lunghezza = velocita_pope * tick_duration
        self.lunghezza += delta_lunghezza
        # Calcolo del peso aggiunto (in kg)
        self.delta_peso_bobina = delta_lunghezza * self.grammatura * larghezza / 1000
        self.peso_bobina += self.delta_peso_bobina
        # Controllo completamento bobina
        if self.lunghezza >= self.lunghezza_max:
            self.completata = True


    def to_dict(self):
        return {
            "grammatura ottenuta": round(self.grammatura, 2),
            "grammatura target": round(self.grammatura_target, 2),
            "lunghezza": round(self.lunghezza, 2),
            "peso_bobina": round(self.peso_bobina, 2),
            "completata": self.completata,
            "indice_qualita": round(self.indice_qualita, 3)
        }

    def __repr__(self):
        return (f"Bobina:\ngrammatura ottenuta = {self.grammatura:.2f} g/m2  \t|\t  Grammatura Target ordine = {self.grammatura_target} g/m2 "
                f"\nlunghezza = {self.lunghezza:.2f} m    \t\t|\t  peso={self.peso_bobina:.2f} kg, "
                f"\ncompletata = {self.completata}  \t\t\t|\t  indice_qualita={self.indice_qualita:.3f}\n")