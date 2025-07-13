import matplotlib.pyplot as plt
from matplotlib.ticker import FuncFormatter, MultipleLocator

class ProgressTracker:
    """
    Classe per la raccolta di dati X-Y destinati a grafici di avanzamento (ordine o simulazione intera).
    Ogni istanza tiene traccia dei valori X (tempo, tick, ecc.) e Y (progresso %, peso cumulato, ecc.).
    """
    def __init__(self, nome, tick_reale):
        """
        :param nome: Nome del tracker (usato come label nel grafico)
        """
        self.tick = tick_reale
        self.nome = nome
        self.x = [0]
        self.y = [0]
        self.x_val = 0

    def aggiorna_di_un_tick(self, y_val):
        """
        Aggiunge un nuovo punto (x, y) al tracker.

        :param x_val: Ascissa (tipicamente tick simulato o tempo)
        :param y_val: Ordinata (percentuale completamento o valore cumulato)
        """
        self.x_val += self.tick
        self.x.append(self.x_val)
        self.y.append(y_val)

    def reset(self):
        """
        Svuota completamente la raccolta dei dati (da usare a fine ordine/simulazione).
        """
        self.x_val = 0
        self.x = [0]
        self.y = [0]

    def get_data(self):
        """
        Ritorna le liste degli X e Y raccolti.

        :return: (x, y) tuple di liste
        """
        return self.x, self.y

    def to_csv(self, filename):
        """
        Esporta i dati X, Y raccolti in formato CSV (con intestazione).
        """
        import csv
        with open(filename, "w", newline='', encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(["x", "y"])
            for xi, yi in zip(self.x, self.y):
                writer.writerow([xi, yi])
        print(f"Dati tracker salvati in {filename}")

def plot_progress(tracker, ylabel="Completamento (%)", savefile=None, show_target=None):
    """
    Plotta l'avanzamento utilizzando i dati X, Y raccolti nel tracker.
    Ogni segmento viene colorato: blu se in salita, rosso se flat, arancione se in discesa.
    L'asse x mostra il tempo simulato in ore con una cifra decimale.
    La griglia è fitta e il grafico parte SEMPRE da (0,0) anche in presenza di dati rumorosi.

    :param tracker: Istanza di ProgressTracker
    :param ylabel: Etichetta asse Y (es. "Completamento (%)", "Peso cumulato (kg)")
    :param savefile: Percorso file per salvataggio PNG. Se None, mostra a schermo.
    :param show_target: (opzionale) Valore target (orizzontale), es: peso totale, per confronto visivo.
    """
    x, y = tracker.get_data()

    # -- PATCH: forza origine vera --
    if len(x) == 0 or x[0] != 0 or y[0] != 0:
        x = [0] + list(x)
        y = [0] + list(y)
    # E anche se per errore ci sono dati negativi, normalizza:
    if x[0] != 0:
        x = [xi - x[0] for xi in x]

    plt.figure(figsize=(20, 6))
    ax = plt.gca()

    # Segment coloring dinamico
    for i in range(1, len(x)):
        xseg = [x[i-1]/3600, x[i]/3600]  # Converte in ore
        yseg = [y[i-1], y[i]]  
        if y[i] > y[i-1]:
            col = "blue"
        elif y[i] == y[i-1]:
            col = "red"
        else:
            col = "orange"
        plt.plot(xseg, yseg, color=col, linewidth=1.0)

    plt.xlabel("Tempo simulato (ore)", fontsize=13)
    plt.ylabel(ylabel, fontsize=13)
    plt.title(f"Avanzamento {tracker.nome}", fontsize=16, pad=18)

    # -- GRIGLIA --
    ax.grid(True, which='major', linestyle='-', alpha=0.18, linewidth=1)
    ax.grid(True, which='minor', linestyle='--', alpha=0.14, linewidth=0.8)
    ax.xaxis.set_minor_locator(MultipleLocator(0.25))  # 15 minuti
    ax.yaxis.set_minor_locator(MultipleLocator(max(1, (max(y)-min(y))/40)))  # dinamico

    plt.tight_layout(pad=2)

    # Formattatore asse x: ore con una cifra decimale
    def format_ore(x, pos=None):
        return f"{x:.1f} h"
    ax.xaxis.set_major_formatter(FuncFormatter(format_ore))

    if show_target is not None:
        plt.axhline(show_target, color='red', linestyle='--', linewidth=1.2, label='Target')

    plt.legend([tracker.nome], loc="upper left", fontsize=11)
    for spine in ax.spines.values():
        spine.set_linewidth(0.7)

    if savefile:
        plt.savefig(savefile, bbox_inches='tight')
        print(f"Grafico salvato come {savefile}")
        plt.close()
    else:
        plt.show()
