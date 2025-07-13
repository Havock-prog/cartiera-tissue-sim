import numpy as np

def calcolo_probabilita_rottura_per_tick(tick_reale_sec, prob_rottura_percentuale, delta_tempo):
    """
    Calcola la probabilità che un evento di rottura (ad esempio, rottura del feltro)
    avvenga nel prossimo intervallo di simulazione (tick), sulla base della probabilità 
    totale di rottura stimata per tutto il tempo residuo di vita utile.

    Principio statistico:
    ---------------------
    Il calcolo si basa sulla legge della probabilità composta per eventi indipendenti
    (processo di Bernoulli a intervalli discreti), 
    e sfrutta la relazione tra probabilità complessiva di accadimento su N intervalli 
    e probabilità elementare per ciascun intervallo.

    Dato che la probabilità di rottura sia distribuita uniformemente su tutto l’arco 
    temporale residuo (ipotesi di omogeneità), la probabilità che l’evento si verifichi
    proprio nel prossimo tick di durata Δt, è ricavata tramite la formula:
        p_tick = 1 - (1 - p_totale) ** (Δt / T)
    dove p_totale è la probabilità totale assegnata sull’intero periodo residuo T.

    Questo approccio riflette la legge della sopravvivenza per eventi rari, 
    utilizzata comunemente nei modelli di affidabilità e manutenzione predittiva.

    """
    if delta_tempo <= 0 or prob_rottura_percentuale <= 0:
        return 0.0
    p_totale = prob_rottura_percentuale / 100
    p_tick = 1 - (1 - p_totale) ** (tick_reale_sec / delta_tempo)
    return p_tick


    

class Feltro:
    MIN_ORE_VITA = 432   # 18 giorni 
    MAX_ORE_VITA = 480   # 20 giorni

    def __init__(self, tick_reale):
        self.usura = np.random.random()
        self.ore_vita = np.random.randint(self.MIN_ORE_VITA, self.MAX_ORE_VITA + 1)
        self.ore_uso = int(self.usura * self.ore_vita)
        self.tick_reale = tick_reale
        self.stato = self.calcola_stato()
        
    def calcola_stato(self):
        """Calcola lo stato attuale in base all'usura."""
        if self.usura >= 0.90:
            self.efficienza = 0.6
            self.prob_rottura = 99.99 #%
            self.probabilita_per_tick = calcolo_probabilita_rottura_per_tick(self.tick_reale, self.prob_rottura, self.ore_vita*3600)
            return "critica"
        elif self.usura >= 0.8:
            self.efficienza = 0.80
            self.prob_rottura = 10 #%
            self.probabilita_per_tick = calcolo_probabilita_rottura_per_tick(self.tick_reale, self.prob_rottura, self.ore_vita*3600)
            return "non-ideale"
        elif self.usura >= 0.5:
            self.efficienza = 0.95
            self.prob_rottura = 5 #%
            self.probabilita_per_tick = calcolo_probabilita_rottura_per_tick(self.tick_reale, self.prob_rottura, self.ore_vita*3600)
            return "buono"
        else:
            self.efficienza = 1
            self.prob_rottura = 1 #%
            self.probabilita_per_tick = calcolo_probabilita_rottura_per_tick(self.tick_reale, self.prob_rottura, self.ore_vita*3600)
            return "eccellente"

    def aggiorna_usura(self):
        """
        Aggiorna l'usura e lo stato del feltro in base alle ore di utilizzo aggiunte.
        """
        self.ore_uso += self.tick_reale/3600  #per convertire tick_reale da secondi ad ore
        self.usura = min(self.ore_uso / self.ore_vita, 1.0)
        self.stato = self.calcola_stato()

    def reset(self):
        self.usura = 0.0
        self.ore_vita = np.random.randint(self.MIN_ORE_VITA, self.MAX_ORE_VITA + 1)
        self.ore_uso = 0
        self.stato = self.calcola_stato()

