import numpy as np


class Ordine:
    def __init__(self, prodotto, grammatura_target, peso_target, altri_parametri=None):
        self.prodotto = prodotto
        self.grammatura_target = grammatura_target
        self.peso_target = peso_target
        self.altri_parametri = altri_parametri or {}

class ProgrammaProduzione:
    def __init__(self, lista_ordini, sigma_velocita=0.10, sigma_efficienza=0.05):
        """
        lista_ordini: lista di oggetti Ordine (o dict)
        sigma_velocita: deviazione standard percentuale rispetto al target velocità
        sigma_efficienza: deviazione standard su parametri randomizzati dagli operatori
        """
        self.lista_ordini = lista_ordini
        self.indice_ordine_corrente = 0
        self.ordine_corrente = self.lista_ordini[0] # tipo : Ordine
        self.sigma_velocita = sigma_velocita
        self.sigma_efficienza = sigma_efficienza
        self.peso_accumulato = 0
        self.peso_parziale = 0
        self.stato_macchina = "ferma"
        self.parametri_processo = {}
        self.transizione_in_corso = False
        

    @staticmethod
    def gauss_riflessa(sigma):
        """
        Gaussiana centrata su 1, con riflessione rispetto a 1 per x > 1.
        Niente limiti: il valore cade 'naturalmente' tra ~0.8 e 1 (99% dei casi),
        con eventi più rari verso 0.75.
        """
        x = np.random.normal(1, sigma)
        if x > 1:
            x = 2 - x
        return x
    
    def imposta_parametri_per_ordine(self):
        """Imposta i parametri per il nuovo ordine, aggiunge randomizzazione e efficienza."""
        ordine = self.ordine_corrente
        # Calcolo della velocità teorica target
        vel_target, conc_impasto = self.calcola_velocita_teorica(ordine.grammatura_target)
        vel_target = round(vel_target,2)
        # Additivi chimici secondo la regola precedente
        prodotto = ordine.prodotto
        if "Carta igienica" in prodotto:
            additivi_chimici = ["sbiancante"]
            grado_raffinazione = 20 #Semplificato da 0 a 100, ove 0 è non raffinata e 100 estremamente raffinata, l'efficacia dipende dalla efficenza dei raffinatori e della cellolusa stessa, ma anche dalle scelte dell'operatore per compensare in corso d'opera
            temperatura_cappa = 410 #°C circa. l'efficienza dipende dalla compensazione e scelte dell'operatore della'efficienza della cappa (appunto spesso compensate dagli operatori se notato in tempo)
        elif "Tovaglioli" in prodotto:
            additivi_chimici = ["sbiancante", "resistenza ad umido (KIMENE)"]
            grado_raffinazione = 30 
            temperatura_cappa = 400
        elif "Asciugatutto" in prodotto:
            additivi_chimici = ["sbiancante", "resistenza ad umido (KIMENE)"]
            grado_raffinazione = 60 
            temperatura_cappa = 450
        # Assegnazione dizionario essenziale
        self.parametri_processo = {
            'velocita tela': {
                "valore":  vel_target,
                "efficienza": self.gauss_riflessa(self.sigma_velocita)  # Maggiore variabilità per la velocita
            },
            'concentrazione impasto %': {
                "valore": conc_impasto,
                "efficienza": self.gauss_riflessa(self.sigma_efficienza)
            },
            'grado raffinazione': {
                "valore": grado_raffinazione,
                "efficienza": np.random.uniform(0.60, 1) # è un parametro nella realtà molto difficile da gestire, dipende da troppi fattori
            },
            'temperatura cappa': {
                "valore": temperatura_cappa,
                "efficienza": self.gauss_riflessa(self.sigma_efficienza)
            },
            'additivi chimici': [
                {
                    "tipologia": additivo,
                    "efficienza": self.gauss_riflessa(self.sigma_efficienza)
                }
                for additivo in additivi_chimici
            ]
        }


    def calcola_velocita_teorica(self, grammatura):
        """
        Calcola la velocità teorica della tela (in m/sec) per una data grammatura,
        scegliendo la concentrazione tra 0,5%, 0,4%, 0,3%, 0,2% che porta la velocità
        più vicina possibile al massimo (senza superare 1800 m/min).
        Restituisce velocità teorica, concentrazione usata e grammatura effettiva che si ottiene.
        """
        portata = 616.67  # L/s (37.000 L/min)
        larghezza = 2.75  # m
        vel_max = 30    # m/sec (1800 m/min)
        concentrazioni = [0.005, 0.004, 0.003, 0.002]
    
        for conc in concentrazioni:
            portata_secca = portata * conc  # kg/s
            # Calcola velocità in m/s
            velocita = portata_secca / ((grammatura / 1000) * larghezza)
            # Solo se NON supera la massima
            if velocita <= vel_max:
                break

        return velocita, conc
    
    def avvia_produzione(self):
        """
        Prepara tutti i parametri di processo e imposta la macchina in stato di produzione.
        Deve essere chiamata ad ogni nuovo ordine.
        """
        self.stato_macchina = "produzione"
        self.imposta_parametri_per_ordine()
        print(
            f"Avvio produzione: {self.ordine_corrente.prodotto} | "
            f"Grammatura target: {self.ordine_corrente.grammatura_target} | "
            f"Velocità tela: {self.parametri_processo['velocita tela']['valore']:.1f} m/min | "
            f"Concentrazione impasto: {self.parametri_processo['concentrazione impasto %']['valore']*100:.2f}%"
        )
        # L’eventuale reset della bobina è ora responsabilità di MacchinaContinua , provvisorio

    def aggiorna_produzione(self, delta_peso_bobina, stato_bobina):
        """
        Aggiorna lo stato dell’ordine corrente sulla base del resoconto proveniente da MacchinaContinua.Bobina.
        """
        if self.stato_macchina != "produzione":
            return

        if  self.peso_parziale >= self.ordine_corrente.peso_target and stato_bobina:
            self.transizione_in_corso = True
            self.ferma_produzione()
            self.peso_parziale = 0
            print(
                f"\nOrdine completato: {self.ordine_corrente.prodotto}. "
                f"Peso richiesto raggiunto"
            )
        else:
            self.peso_accumulato += delta_peso_bobina
            self.peso_parziale += delta_peso_bobina

    def ferma_produzione(self):
        self.stato_macchina = "ferma"
        print("\nProduzione FERMA. Setup nuovo ordine in corso...\n")

    def prepara_prossimo_ordine(self):
        """Passa al prossimo ordine, o termina."""
        self.indice_ordine_corrente += 1
        if self.indice_ordine_corrente >= len(self.lista_ordini):
            return "Tutti gli ordini completati. Termine Simulazione"
        else:
            self.ordine_corrente = self.lista_ordini[self.indice_ordine_corrente]
            self.transizione_in_corso = False
            # Puoi inserire qui logica di setup/attesa/reset ecc.
            self.avvia_produzione()
            return "Cambio produzione in corso"
        

