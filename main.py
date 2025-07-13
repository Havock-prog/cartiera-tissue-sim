"""
MAIN SIMULAZIONE CARTIERA – Project WOrk (UNIPEGASO)
Gestione completa di una simulazione multi-ordine su MacchinaContinua,
con logging strutturato e snapshot periodici.
"""
import numpy as np
import time
from core.macchinacontinua import MacchinaContinua
from core.programmaproduzione import Ordine
from core.reportstatistica import ReportStatistica

def input_tick_visivo():
    """
    Richiede all’utente di inserire l’intervallo di aggiornamento visuale (in secondi simulati).
    Questo parametro determina ogni quanto la simulazione aggiorna e stampa le informazioni di avanzamento
    (es. stato della macchina, statistiche, eventi), aggregando internamente più cicli di simulazione.
    L’intervallo deve essere multiplo del passo di simulazione interno e almeno pari a 5 secondi.
    """
    while True:
        try:
            val = int(input("Immetti l'INTERVALLO DI AGGIORNAMENTO VISUALE (in secondi simulati, minimo 5, multiplo di 5): "))
            if val < 5:
                print("Valore troppo basso! Inserire almeno 5.")
                continue
            if val % 5 != 0:
                val = round(val / 5) * 5
                print(f"Tick visivo arrotondato al multiplo più vicino: {val}")
            return val
        except ValueError:
            print("Input non valido. Inserisci un numero intero.")

def genera_ordini_randomici():
    """
    Crea la lista dei 3 ordini randomici (igienica, asciugatutto, tovaglioli),
    con grammature e pesi nei range specificati dal committente.
    Ordina e mischia la lista prima della simulazione.
    """
    # Range in KG (da tonnellate)
    peso_min = 20000
    peso_max = 45000
    ordini = [
        Ordine(
            prodotto="Carta igienica",
            grammatura_target=round(np.random.uniform(16, 19), 1),
            peso_target=np.random.randint(peso_min, peso_max+1)
        ),
        Ordine(
            prodotto="Tovaglioli",
            grammatura_target=round(np.random.uniform(14, 16), 1),
            peso_target=np.random.randint(peso_min, peso_max+1)
        ),
        Ordine(
            prodotto="Asciugatutto",
            grammatura_target=round(np.random.uniform(26, 30+1), 1),
            peso_target=np.random.randint(peso_min, peso_max+1)
        ),
    ]
    np.random.shuffle(ordini)
    return ordini

def formatta_tempo(secondi):
    ore = int(secondi // 3600)
    minuti = int((secondi % 3600) // 60)
    sec = int(secondi % 60)
    return f"{ore}h {minuti}m {sec}s"


def main():
    print("\n==== SIMULAZIONE PRODUZIONE CARTIERA – AVVIO ====")
    print("\n\nGENERAZIONE ORDINI CASUALI:")
    lista_ordini = genera_ordini_randomici()
    for idx, ordine in enumerate(lista_ordini, 1):
        print(f" Ordine {idx+1}: {ordine.prodotto} | Grammatura target: {ordine.grammatura_target} g/m2 | Peso target: {ordine.peso_target/1000:.1f} t")
    print("\n--- Simulazione in corso ---\n")
    print(
    "NOTA: Questa simulazione adotta una logica di tempo accelerato per consentire l’analisi rapida della produzione cartaria.\n"
    "Il passo interno della simulazione (tick reale) è fissato a 5 secondi: ciò significa che, ad ogni ciclo interno,\n"
    "vengono simulati 5 secondi di attività reale della cartiera.\n\n"
    "L’utente può selezionare un intervallo di aggiornamento (ad es. 120): questo valore determina ogni quanto tempo\n"
    "simulato la simulazione aggiorna e mostra i risultati. Se, ad esempio, l’intervallo è impostato a 120,\n"
    "ogni secondo reale di esecuzione del programma corrisponde a 120 secondi (2 minuti) di produzione simulata.\n"
    "Il fattore minimo di accelerazione è 5x (ogni secondo reale equivale ad almeno 5 secondi simulati), ma può essere impostato su valori più elevati\n"
    "per accelerare l’analisi di scenari produttivi estesi, mantenendo comunque la risoluzione degli eventi a livello di 5 secondi.\n"
    )
    # 2. Input tick visivo
    tick_visivo = input_tick_visivo()
    tick_reale = 5  #sec, fisso

    # 3. Istanzia la macchina continua
    macchina = MacchinaContinua(lista_ordini, tick_visivo=tick_visivo, tick_reale=tick_reale)
    macchina.setup_bobina()
    # 4. Logging: snapshot periodici
    log_snapshots = []
    log_snapshots_settings_macchina = []
    n_tick_per_visivo = tick_visivo // tick_reale
    tempo = 0
    ReportStatistica.vista_macchina_efficienze(macchina)
    stato_json = ReportStatistica.json_efficienze_macchina(macchina)
    log_snapshots_settings_macchina.append(stato_json)

    while True:
        # Esegui tick per tutta la durata del tick visivo
        for _ in range(n_tick_per_visivo):
            macchina.esegui_tick()
            # Puoi inserire qui logging per ogni singolo tick reale se vuoi
            if macchina.stato == "Tutti gli ordini completati. Termine Simulazione":
                print()
                print(f"{macchina.stato}")
                break
            if macchina.stato == "Cambio produzione in corso":
                ReportStatistica.vista_macchina_efficienze(macchina)
                stato_json = ReportStatistica.json_efficienze_macchina(macchina)
                log_snapshots_settings_macchina.append(stato_json)
                break

        # Snapshot a ogni tick visivo
      

        print ("\n-----------------------------------------------------------------\n")
        print(f"{macchina.stato}" )
        print(f"tempo di fermo: {formatta_tempo(macchina.evento.tot_timer)} --- tempo simulazione {formatta_tempo(tempo+1)} --- tempo simulato: {formatta_tempo(macchina.simclock.get_time())}")
        print(f"Tempo totale perso: {formatta_tempo(macchina.tempo_perso)}")
        if macchina.stato == "Tutti gli ordini completati. Termine Simulazione":
            break
        ReportStatistica.vista_rapida(macchina)
        stato_json = ReportStatistica.json_rapida(macchina)
        log_snapshots.append(stato_json)
        # *** Pausa reale di un secondo tra un ciclo e l'altro ***
        time.sleep(1)
        tempo += 1
    # Salva il grafico finale di tutta la simulazione PRIMA di uscire!
    ReportStatistica.grafico_simulazione(
        macchina.tracker_simulazione,
        nome_file="grafico_simulazione_totale.png"
    )
 
    # 5. Salvataggio finale dei log

    import json

    with open("log_simulazione.json", "w") as f:
        json.dump(log_snapshots, f, indent=2)
  
    with open("log_bobine.json", "w") as f:
        json.dump(macchina.log_bobine, f, indent=2)

    with open("log_stats_macchina.json", "w") as f:
        json.dump(log_snapshots_settings_macchina, f, indent=2)

    with open("log_eventi_dettagliati.json", "w") as f:
        json.dump(ReportStatistica.json_eventi(macchina), f, indent=2)
    tempo_simulato = macchina.simclock.get_time()
    print(f"\n\n==== SIMULAZIONE CONCLUSA ====")
    print(f"\nTempo totale Simulazione: {formatta_tempo(tempo)} ({tempo} secondi)")
    print(f"Tempo totale Simulato: {formatta_tempo(tempo_simulato)} ({tempo_simulato} secondi) di cui {formatta_tempo(macchina.tempo_perso)} ({macchina.tempo_perso} secondi) di non produzione continua") 
    print(f"Percentuale tempo in Produzione: {100-round((macchina.tempo_perso/tempo_simulato)*100, 1)}%")
    print(f"Totale tonnellate Carta prodotta: {macchina.programma.peso_accumulato/1000:.1f} t")
    # Stampa numero di bobine prodotte per ordine
    print("\nNumero di bobine prodotte per ordine:")
    for idx, n_bobine in enumerate(macchina.bobine_tot_prodotte):
        nome_prodotto = macchina.programma.lista_ordini[idx].prodotto
        print(f"  Ordine {idx+1} ({nome_prodotto}): {n_bobine} bobine")
    # Numero totale di bobine prodotte
    totale_bobine = sum(macchina.bobine_tot_prodotte)
    print(f"\nNumero totale di bobine prodotte: {totale_bobine} (in tempo totale Simulato)")
    print("\n\nGrafici ordini e simulazione complessiva salvati come PNG")
    print("Log snapshot periodici salvato in log_simulazione.json")
    print("Log finale bobine prodotte salvato in log_bobine.json")
    print("Log finale parametri produzione salvato in log_stats_macchina.json.")

if __name__ == "__main__":
    main()
