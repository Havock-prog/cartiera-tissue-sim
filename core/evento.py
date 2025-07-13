import numpy as np

def roll_evento(probabilita):
    """
    Esegue un roll su una probabilità (tra 0 e 1).
    Restituisce True se l’evento si verifica, False altrimenti.
    """
    return np.random.random() < probabilita



def calcolo_probabilita_per_tick(tick_reale_sec, prob_evento, range_tempo_sec):
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
    p_totale = prob_evento / 100
    p_tick = 1 - (1 - p_totale) ** (tick_reale_sec / range_tempo_sec)
    return p_tick




class Evento:
    def __init__(self, tick_reale, macchina):
        self.tipo = None                 # es: "rottura_feltro", "guasto_generale"
        self.cambio_feltro = None        # durata residua evento se attivo (in tick)
        self.tick_reale = tick_reale
        # Calcolo della probabilità  in un tick da 5 secondi che si verifichi un guasto macchina...  
        # ...che in media si verifica al 50% in 10 giorni convertito in secondi
        self.probabilita_tick_guasto = calcolo_probabilita_per_tick(self.tick_reale, 50 , 10*24*3600) 
        #50% ogni 4 ore
        self.probabilita_tick_rottura_carta = calcolo_probabilita_per_tick(self.tick_reale, 50 , 4*3600)
        #probabilita di rottura specifico durante ogni cambio bobina, estremamente più elevato rispetto al solito
        self.probabilita_tick_carta_special = calcolo_probabilita_per_tick(self.tick_reale, 10 , 15)
        self.eventi_attivi = []
        # timer che rapresentano il tempo ogni quanto la quale è necessario cambiare il componente
        self.timer_lama_crespatura = np.random.randint(22,27+1)*3600 #tra le 22 e le 27 ore
        self.timer_rimanente_LC = self.timer_lama_crespatura
        self.timer_pulizia_macchina = 28800 #secondi, 8 ore
        self.timer_rimanente_pulizia = self.timer_pulizia_macchina
        self.timer_fine_vita_feltro = int((macchina.feltro.ore_vita-macchina.feltro.ore_uso)*3600)
        self.timer_rimanente_feltro = self.timer_fine_vita_feltro
        self.tot_timer = 0
        self.log_eventi = []
        self.macchina = macchina

    def pulizia_macchina_extra (self):
        if np.random.random() > 0.60 :
            self.timer_rimanente_pulizia = self.timer_pulizia_macchina
            return np.random.randint(210, 360+1)
        else:
            return 0


    def gestione_passivi(self):
        """
        Gestisce gli eventi passivi casuali: rottura feltro e guasto macchina.
        A ogni tick vengono effettuati due roll casuali, uno per ciascun evento.
        Se uno o entrambi si verificano, l’evento viene registrato e viene calcolato il tempo di fermo associato.
        """
        if not self.eventi_attivi:
            trigger_feltro = roll_evento(self.macchina.feltro.probabilita_per_tick)
            if trigger_feltro:
                self.eventi_attivi.append("cambio feltro")

            trigger_guasto = roll_evento(self.probabilita_tick_guasto)
            if trigger_guasto:
                self.eventi_attivi.append("guasto macchina")

            trigger_carta = roll_evento(self.probabilita_tick_rottura_carta)
            if trigger_carta:
                self.eventi_attivi.append("rottura carta")

            if self.eventi_attivi:
                self.gestione_attivi()

        elif "cambio bobina" in self.eventi_attivi:
            trigger_carta = roll_evento(self.probabilita_tick_carta_special)
            if trigger_carta:
                self.eventi_attivi.append("rottura carta")
                self.gestione_attivi()
     

    def reset(self):
        if "cambio feltro" in self.eventi_attivi:
            self.macchina.feltro.reset()
            self.timer_fine_vita_feltro = int((self.macchina.feltro.ore_vita-self.macchina.feltro.ore_uso)*3600)
            self.timer_rimanente_feltro = self.timer_fine_vita_feltro
        if "pulizia macchina" in self.eventi_attivi:
            self.timer_rimanente_pulizia = self.timer_pulizia_macchina
        if "cambio lama crespatura" in self.eventi_attivi:
            self.timer_lama_crespatura = np.random.randint(22,27+1)*3600 
            self.timer_rimanente_LC = self.timer_lama_crespatura
        self.eventi_attivi = []


    def gestione_attivi(self):
        ordine_corrente = self.macchina.programma.ordine_corrente.prodotto
        indice_bobina = self.macchina.bobine_tot_prodotte[self.macchina.indice]
        tempo_simulato_corrente = self.macchina.simclock.get_time()
        if "cambio feltro" in self.eventi_attivi:
            tempo_effetivo_cambio_feltro = int(np.random.normal(7200, 900))
            self.tot_timer = max(self.tot_timer, tempo_effetivo_cambio_feltro)
            self.log_eventi.append({
                "evento": "cambio feltro",
                "durata": tempo_effetivo_cambio_feltro,
                "tempo_simulato": tempo_simulato_corrente,
                "ordine_corrente": ordine_corrente,
                "indice_bobina": indice_bobina
            })

        if "guasto macchina" in self.eventi_attivi:
            tempo_effetivo_riparazione_macchina = np.random.randint(300, 21600+1)
            self.tot_timer = max(self.tot_timer, tempo_effetivo_riparazione_macchina)
            self.log_eventi.append({
                "evento": "guasto macchina",
                "durata": tempo_effetivo_riparazione_macchina,
                "tempo_simulato": tempo_simulato_corrente,
                "ordine_corrente": ordine_corrente,
                "indice_bobina": indice_bobina
            })

        if "rottura carta" in self.eventi_attivi:
            tempo_rottura_carta = np.random.randint(60, 420+1)
            self.tot_timer = max(self.tot_timer, tempo_rottura_carta)
            self.log_eventi.append({
                "evento": "rottura carta",
                "durata": tempo_rottura_carta,
                "tempo_simulato": tempo_simulato_corrente,
                "ordine_corrente": ordine_corrente,
                "indice_bobina": indice_bobina
            })

        if "pulizia macchina" in self.eventi_attivi:
            tempo_pulizia_macchina = np.random.randint(210, 390+1)
            self.tot_timer = max(self.tot_timer, tempo_pulizia_macchina)
            self.log_eventi.append({
                "evento": "pulizia macchina",
                "durata": tempo_pulizia_macchina,
                "tempo_simulato": tempo_simulato_corrente,
                "ordine_corrente": ordine_corrente,
                "indice_bobina": indice_bobina
            })

        if "cambio lama crespatura" in self.eventi_attivi:
            tempo_cambio_lama_crespatura = np.random.randint(240, 360+1)
            self.tot_timer = max(self.tot_timer, tempo_cambio_lama_crespatura)
            self.log_eventi.append({
                "evento": "cambio lama crespatura",
                "durata": tempo_cambio_lama_crespatura,
                "tempo_simulato": tempo_simulato_corrente,
                "ordine_corrente": ordine_corrente,
                "indice_bobina": indice_bobina
            })

        if "cambio bobina" in self.eventi_attivi:
            tempo_cambio_bobina = 15
            self.tot_timer = max(self.tot_timer, tempo_cambio_bobina)
            self.log_eventi.append({
                "evento": "cambio bobina",
                "durata": tempo_cambio_bobina,
                "tempo_simulato": tempo_simulato_corrente,
                "ordine_corrente": ordine_corrente,
                "indice_bobina": indice_bobina
            })

        if "cambio produzione" in self.eventi_attivi:
            tempo_cambio_produzione = np.random.randint(900, 1500+1)
            self.tot_timer = max(self.tot_timer, tempo_cambio_produzione)
            self.log_eventi.append({
                "evento": "cambio produzione",
                "durata": tempo_cambio_produzione,
                "tempo_simulato": tempo_simulato_corrente,
                "ordine_corrente": ordine_corrente,
                "indice_bobina": indice_bobina
            })

        if self.tot_timer != 0 and "cambio bobina" not in self.eventi_attivi:
            tempo_extra = self.pulizia_macchina_extra()
            if tempo_extra > 0:
                self.tot_timer += tempo_extra
                self.log_eventi.append({
                    "evento": "pulizia macchina extra",
                    "durata": tempo_extra,
                    "tempo_simulato": tempo_simulato_corrente,
                    "ordine_corrente": ordine_corrente,
                    "indice_bobina": indice_bobina
                })

         

    def eventi_temporali(self):
        if "cambio feltro" not in self.eventi_attivi:
            self.timer_rimanente_feltro -= self.tick_reale
            if self.timer_rimanente_feltro <= 0:
                self.eventi_attivi.append("cambio feltro")

        if "pulizia macchina" not in self.eventi_attivi:
            self.timer_rimanente_pulizia -= self.tick_reale
            if self.timer_rimanente_pulizia <= 0:
                self.eventi_attivi.append("pulizia macchina")

        if "cambio lama crespatura" not in self.eventi_attivi:
            self.timer_rimanente_LC -= self.tick_reale
            if self.timer_rimanente_LC <= 0: 
                self.eventi_attivi.append("cambio lama crespatura")

        if self.eventi_attivi:
            self.gestione_attivi()

            
 
