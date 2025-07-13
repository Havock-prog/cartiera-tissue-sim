from core.bobina import Bobina                # Gestione singola bobina prodotta
from core.feltro import Feltro                # Gestione feltro/sezione presse
from core.evento import Evento                # Gestione eventi (guasti, fermi, ecc.)
from core.programmaproduzione import ProgrammaProduzione, Ordine  # Logica ordini e gestione processo
from core.reportstatistica import ReportStatistica 
from core.simclock import SimClock
from core.tracker import ProgressTracker


def calcola_media_ponderata_efficienze(parametri, efficienza_feltro):
    """
    Calcola la media ponderata delle efficienze dei parametri di processo,
    includendo anche l’efficienza del feltro con peso specifico.
    """
    # Scelta arbitraria dei pesi del programmatore
    pesi_default = {
        'velocita tela': 3,
        'concentrazione impasto %': 2,
        'grado raffinazione': 4,
        'temperatura cappa': 1,
        # Additivi: puoi dare pesi diversi ai singoli additivi se vuoi!
        'additivo_0': 1,
        'additivo_1': 1,
        'additivo_2': 1,
        'feltro': 3  # peso speciale per l’efficienza feltro
    }
    efficienze = []
    pesi_eff = []
    # Parametri principali
    for chiave, valore in parametri.items():
        if chiave != "additivi chimici":
            efficienze.append(valore["efficienza"])
            pesi_eff.append(pesi_default.get(chiave, 1))
    # Additivi chimici
    for idx, additivo in enumerate(parametri.get("additivi chimici", [])):
        efficienze.append(additivo["efficienza"])
        nome = f"additivo_{idx}"
        pesi_eff.append(pesi_default.get(nome, 1))
    # Aggiungi efficienza feltro con peso dedicato
    efficienze.append(efficienza_feltro)
    pesi_eff.append(pesi_default.get("feltro", 3))
    numeratore = sum(e * p for e, p in zip(efficienze, pesi_eff))
    denominatore = sum(pesi_eff) if pesi_eff else 1
    return numeratore / denominatore

def sigma_grammatura_solo_eff(grammatura_target, efficienza_media, coeff, p):
    """
    Calcola la deviazione standard (sigma) della grammatura prodotta in funzione dell’efficienza media.
    La formula penalizza quadraticamente le basse efficienze, simulando la crescita della variabilità produttiva.
    coeff regola il massimo impatto dell’inefficienza; p l’intensità della penalizzazione.
    """
    ineff = max(0, 1 - efficienza_media)
    return grammatura_target * coeff * (ineff ** p)


class MacchinaContinua:
    def __init__(self, lista_ordini, tick_visivo,  tick_reale=5, larghezza_macchina=2.75):
        self.stato = "Produzione"
        self.tick_reale = tick_reale                # Esempio: 5 secondi per tick
        self.tick_visivo = tick_visivo               
        self.feltro = Feltro(tick_reale)                      # Feltro iniziale
        self.bobina = None
        self.sigma = None                          # Bobina inizializzata in seguito  
        self.programma = ProgrammaProduzione(lista_ordini)
        self.programma.avvia_produzione()             # Oggetto ProgrammaProduzione già avviato
        self.report = ReportStatistica()     # idem, deve essere un oggetto
        self.simclock = SimClock(tick_interno=self.tick_reale, tick_visivo=self.tick_visivo) # Clock simulato: usi solo il tick interno, che rappresenta il tempo reale di simulazione
        self.larghezza_macchina = larghezza_macchina # Statico, tipico 2.75 m
        self.tracker_ordine = ProgressTracker("Tracker produzione ordine corrente", self.tick_reale)
        self.tracker_simulazione = ProgressTracker("tracker produzione simulazione", self.tick_reale)
        self.indice = 0
        self.bobine_tot_prodotte = [0, 0, 0]
        self.log_bobine = []
        self.tempo_perso = 0  # Nuovo contatore tempo perso totale
        self.evento = Evento(tick_reale, self)
        self.eventi_attivi = self.evento.eventi_attivi               # se serve un oggetto evento, non la classe
        
        

    def setup_ordine(self):
        """
        Setup parametri per il nuovo ordine (solo al cambio ordine).
        Inizializza la prima bobina col nuovo ordine.
        """
        self.programma.imposta_parametri_per_ordine()
        self.setup_bobina()  # Prima bobina del nuovo ordine

    def setup_bobina(self):
        """
        Crea una nuova bobina per l’ordine corrente, sigma e qualità
        dipendenti dallo stato effettivo del feltro (anche a metà ordine).
        """
        ordine = self.programma.ordine_corrente
        grammatura = ordine.grammatura_target
        lunghezza_max = getattr(ordine, "lunghezza_max", 50000)
        eff_media = calcola_media_ponderata_efficienze(self.programma.parametri_processo, self.feltro.efficienza)
        sigma = sigma_grammatura_solo_eff(grammatura, eff_media, coeff=0.6, p=2)
        self.bobina = Bobina(grammatura, sigma, eff_media, lunghezza_max)



    def esegui_tick(self):
        """Avanza l'intera simulazione di un tick."""
        # 1. Aggiorna clock simulato
        self.simclock.advance_internal()
        
        if self.evento.tot_timer != 0:
            self.stato = "non in Produzione: cambio, manutenzione o guasto"
            self.tempo_perso += self.tick_reale
            self.evento.tot_timer = max(0, self.evento.tot_timer - self.tick_reale)
            progresso = min(100.0, 100*self.programma.peso_parziale/self.programma.ordine_corrente.peso_target)
            self.tracker_ordine.aggiorna_di_un_tick(progresso)
            self.tracker_simulazione.aggiorna_di_un_tick(self.programma.peso_accumulato/1000)
            if self.evento.tot_timer == 0:
                self.evento.reset()
                self.eventi_attivi = self.evento.eventi_attivi
            return
  
        else:
            self.evento.eventi_temporali()
            # 2. Gestisci eventi (fermi, guasti ecc)
            self.evento.gestione_passivi()
            if self.evento.tot_timer > 0:
                self.eventi_attivi = self.evento.eventi_attivi
                progresso = min(100.0, 100*self.programma.peso_parziale/self.programma.ordine_corrente.peso_target)
                self.tracker_ordine.aggiorna_di_un_tick(progresso)
                self.tracker_simulazione.aggiorna_di_un_tick(self.programma.peso_accumulato/1000)
                return
            # 3. Stato normale: avanzamento produzione bobina
            if not self.bobina.completata :
                # Avanza usura feltro PRIMA di produrre (così il nuovo sigma sarà aggiornato)
                self.stato = "Produzione"
                self.feltro.aggiorna_usura()
                self.bobina.aggiorna_peso(self.tick_reale, self.programma.parametri_processo['velocita tela']['valore'], larghezza=self.larghezza_macchina)
                self.programma.aggiorna_produzione(self.bobina.delta_peso_bobina, self.bobina.completata)
                self.bobina.delta_peso_bobina = 0
                progresso = min(100.0, 100*self.programma.peso_parziale/self.programma.ordine_corrente.peso_target)
                self.tracker_ordine.aggiorna_di_un_tick(progresso)
                self.tracker_simulazione.aggiorna_di_un_tick(self.programma.peso_accumulato/1000)
                
            # 4. Bobina completata!
            elif self.bobina.completata :
                self.programma.aggiorna_produzione(self.bobina.delta_peso_bobina, self.bobina.completata)
                self.bobine_tot_prodotte[self.indice] += 1
                self.log_bobine.append(ReportStatistica.json_bobina(self.bobina))
                # Aggiorna usura feltro per l'ultimo tick di produzione
                self.feltro.aggiorna_usura()
                progresso = min(100.0, 100*self.programma.peso_parziale/self.programma.ordine_corrente.peso_target)
                self.tracker_ordine.aggiorna_di_un_tick(progresso)
                self.tracker_simulazione.aggiorna_di_un_tick(self.programma.peso_accumulato/1000)
                if self.programma.stato_macchina == "produzione":
                    self.stato = "cambio bobina"
                    if self.feltro.stato == "critica": # cambia bobina e feltro
                        self.evento.eventi_attivi.append ("cambio feltro") 
                        self.evento.eventi_attivi.append ("cambio bobina")
                    else:
                        self.evento.eventi_attivi.append ("cambio bobina")
                    self.eventi_attivi = self.evento.eventi_attivi
                    self.evento.gestione_attivi()
                    self.setup_bobina() # cambia solo la bobina
       
                elif self.programma.stato_macchina == "ferma":
                    self.evento.eventi_attivi.append("cambio produzione")
                    self.eventi_attivi = self.evento.eventi_attivi
                    self.evento.gestione_attivi()
                    nome_ordine = self.programma.ordine_corrente
                    ReportStatistica.grafico_avanzamento_ordine(
                        self.tracker_ordine,
                        nome_file=f"grafico_ordine_{self.indice+1}_{nome_ordine.prodotto}.png"
                    )
                    self.stato = self.programma.prepara_prossimo_ordine()
                    self.indice += 1
                    self.setup_ordine()  # cambia ordine e bobina
                    self.tracker_ordine.reset()
             

            
        