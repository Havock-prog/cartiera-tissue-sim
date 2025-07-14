from core.tracker import plot_progress

def formatta_tempo(secondi):
    ore = int(secondi // 3600)
    minuti = int((secondi % 3600) // 60)
    sec = int(secondi % 60)
    return f"{ore}h {minuti}m {sec}s"


class ReportStatistica:
    """
    Classe per la creazione rapida di viste statistiche e grafiche della simulazione cartiera.
    """

    @staticmethod
    def vista_bobina(macchina):
        """Vista dettagliata della bobina corrente."""
        print("\n=== Stato Bobina Corrente ===")
        print(macchina.bobina.__repr__())
        if macchina.indice < len(macchina.bobine_tot_prodotte):
            print(f"Bobine prodotte nell'ordine corrente: {macchina.bobine_tot_prodotte[macchina.indice]}")
        else:
            print("(fine ordini)")
        print()

    @staticmethod
    def vista_macchina_efficienze(macchina):
        """
        Vista dello stato macchina: per ogni variabile, stampa anche l’efficienza associata (se presente), 
        in formato ordinato e leggibile come da esempio desiderato.
        """
        print("=== Stato Macchina Continua (con efficienze) ===")
        eventi = macchina.eventi_attivi
        parametri = macchina.programma.parametri_processo
        feltro = macchina.feltro
        stato_macchina = macchina.stato

        if ("guasto macchina" in eventi) or ("cambio feltro" in eventi):
            fermo = True
        else:
            fermo = False

        # Velocità, concentrazione, raffinazione, temperatura: stampati con label e unità
        mapping = {
            'velocita tela':   ("Velocità tela",         "m/s",        1),
            'concentrazione impasto %': ("Concentrazione impasto %", "", 3),
            'grado raffinazione': ("Grado raffinazione (0-100)",      "", 0),
            'temperatura cappa': ("Temperatura cappa",   "°C",         0)
        }

        for key, info in parametri.items():
            if key == "additivi chimici":
                print("Additivi chimici:")
                for additivo in info:
                    print(f"  - {additivo['tipologia']:<30} | efficienza: {additivo['efficienza']:.3f}")
            else:
                label, um, nd = mapping.get(key, (key.capitalize(), "", 2))
                valore = info["valore"]
                efficienza = info.get("efficienza", None)
                valore_display = 0 if fermo else valore
                if nd == 0:
                    valore_fmt = f"{int(valore_display)}"
                elif nd == 1:
                    valore_fmt = f"{valore_display:.1f}"
                else:
                    valore_fmt = f"{valore_display:.3f}"
                unita = f" {um}" if um else ""
                print(f"{label:<30}: {valore_fmt}{unita:<4} | efficienza: {efficienza:.3f}")

        print(f"Usura feltro: {feltro.usura*100:.1f}% | efficienza: {feltro.efficienza:.3f}")
        print(f"Stato: {stato_macchina}")
        print(f"Eventi attivi: {eventi}")
        print()


    @staticmethod
    def vista_avanzamento_ordine(macchina):
        """
        Vista avanzamento ordine: percentuale completata, target vs attuale.
        """
        ordine = macchina.programma.ordine_corrente
        peso_parziale = macchina.programma.peso_parziale
        peso_target = ordine.peso_target
        progresso = min(100.0, 100 * peso_parziale / peso_target) if peso_target else 0.0 
        print("=== Avanzamento Ordine Corrente ===")
        print(f"Prodotto: {ordine.prodotto}")
        print(f"Peso attuale: {peso_parziale:.1f} kg / Target: {peso_target:.1f} kg")
        print(f"Avanzamento: {progresso:.2f}%")
        if macchina.indice < len(macchina.bobine_tot_prodotte):
            print(f"Bobine completate: {macchina.bobine_tot_prodotte[macchina.indice]}")
        else:
            print()
        print()

    @staticmethod
    def vista_rapida(macchina):
        """
        Stampa tutte le viste essenziali con un unico comando.
        """
        ReportStatistica.vista_bobina(macchina)
        ReportStatistica.vista_macchina_efficienze(macchina)
        ReportStatistica.vista_avanzamento_ordine(macchina)
        ReportStatistica.vista_eventi(macchina)

    
    @staticmethod
    def vista_eventi(macchina):
        if macchina.stato == "Tutti gli ordini completati. Termine Simulazione":
            return
        print("\n=== Ultimi 3 Eventi (Guasti/Cambi/Manutenzione) ===")
        eventi = macchina.evento.log_eventi[-3:]  # prendi ultimi tre (o tutti se <3)
        if not eventi:
            print("(Nessun evento registrato)")
        else:
            for evento in eventi:
                print(
                    f"[{evento['evento'].upper()}] durata: {formatta_tempo(evento['durata'])}, "
                    f"tempo simulato: {formatta_tempo(evento['tempo_simulato'])}, "
                    f"ordine: {evento['ordine_corrente']}, bobina n°: {evento['indice_bobina']}"
                )
        print(f"\nTempo totale perso: {formatta_tempo(macchina.tempo_perso)}\n")

    
    # --- METODI GRAFICI (INTEGRAZIONE CON TRACKER) ---
    @staticmethod
    def grafico_avanzamento_ordine(progress_tracker, nome_file=None):
        """
        Genera e salva/mostra il grafico di avanzamento ordine corrente.
        """
        plot_progress(progress_tracker, ylabel="Completamento (%)", savefile=nome_file, show_target=100)

    @staticmethod
    def grafico_simulazione(progress_tracker, peso_totale=None, nome_file=None):
        """
        Genera e salva/mostra il grafico di avanzamento per l'intera simulazione.
        """
        label = "Peso prodotto (t)"
        plot_progress(progress_tracker, ylabel=label, savefile=nome_file, show_target=peso_totale)

    # --- Metodi JSON ---

    @staticmethod
    def json_bobina(bobina):
        # Nessuna modifica, già coerente col __repr__ (usando to_dict)
        return bobina.to_dict()

    def json_efficienze_macchina(macchina):
        """
        Restituisce un dizionario con tutte le efficienze dei parametri di processo e del feltro.
        Gestisce 'fermo' come nel resto del codice (velocità, temperatura ecc. messi a 0 se fermo).
        """
        parametri = macchina.programma.parametri_processo
        feltro = macchina.feltro
        eventi = macchina.eventi_attivi

        if ("guasto macchina" in eventi) or ("cambio feltro" in eventi):
            fermo = True
        else:
            fermo = False

        efficienze = {}
        for key, info in parametri.items():
            if key == "additivi chimici":
                efficienze_additivi = []
                for additivo in info:
                    efficienze_additivi.append({
                        "tipologia": additivo["tipologia"],
                        "efficienza": additivo["efficienza"]
                    })
                efficienze["additivi_chimici"] = efficienze_additivi
            else:
                # Mostra efficienza normalmente, ma segnala valore=0 se la macchina è ferma (come per la vista)
                valore = 0 if fermo else info.get("valore", None)
                efficienza = info.get("efficienza", None)
                efficienze[key] = {
                    "valore": valore,
                    "efficienza": efficienza
                }

        efficienze["feltro"] = {
            "usura": feltro.usura,
            "efficienza": getattr(feltro, "efficienza", None)
        }
        return efficienze

    @staticmethod
    def json_avanzamento_ordine(macchina):
        ordine = macchina.programma.ordine_corrente
        peso_parziale = macchina.programma.peso_parziale
        peso_target = ordine.peso_target
        progresso = min(100.0, 100 * peso_parziale / peso_target) if peso_target else 0.0 
        return {
            "prodotto": ordine.prodotto,
            "peso_attuale_kg": peso_parziale,
            "peso_target_kg": peso_target,
            "avanzamento_percentuale": progresso,
            "Bobine completate": macchina.bobine_tot_prodotte[macchina.indice]
        }

    @staticmethod
    def json_rapida(macchina):
        return {
            "bobina": ReportStatistica.json_bobina(macchina.bobina),
            "macchina": ReportStatistica.json_efficienze_macchina(macchina),
            "avanzamento_ordine": ReportStatistica.json_avanzamento_ordine(macchina),
            "lista eventi": ReportStatistica.json_eventi(macchina)
        }
    

    @staticmethod
    def json_eventi(macchina):
        return {
            "eventi": macchina.evento.log_eventi,
            "tempo_totale_perso_sec": macchina.tempo_perso
        }