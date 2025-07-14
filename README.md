# Simulatore Processo Produttivo Cartario Tissue

Simulatore Python di un processo produttivo cartario tissue (Macchina Continua), sviluppato come Project Work per il corso di Informatica per le Aziende Digitali (L-31) – UniPegaso.

---

## Descrizione

Questo progetto simula la produzione industriale di bobine di carta tissue tramite una rappresentazione realistica e parametrica della Macchina Continua.  
Il simulatore permette di modellare più prodotti (carta igienica, asciugatutto, tovaglioli, ecc.) e di analizzare l’impatto di variabili operative, eventi casuali, manutenzioni e scelte umane sulla produttività, l’efficienza e la qualità finale del prodotto.

Il modello integra elementi stocastici, eventi di guasto (secondo distribuzioni di Bernoulli), oscillazioni di efficienza modellate tramite una “gaussiana riflessa” attorno all’equilibrio, e consente di studiare in dettaglio sia l’evoluzione temporale del processo sia gli effetti delle strategie operative o manutentive.

---

## Contenuto

- Codice Python a oggetti (OOP), suddiviso per classi (MacchinaContinua, Feltro, Evento, Bobina, ecc.).
- Moduli per:
  - Simulazione dei lotti multiprodotto
  - Gestione eventi stocastici e manutenzioni
  - Raccolta e reportistica avanzata dei risultati (grafici, json, output tabellari)
- Esempio di input/output e grafici
- Documentazione e riferimenti bibliografici di processo reale

---

## Requisiti

- Python 3.11+
- Numpy
- Matplotlib

> Installa le dipendenze richieste con:
> ```bash
> pip install numpy matplotlib
> ```

---

## Come si esegue

1. **Scarica o clona il repository**
2. **Avvia il file `main.py`** (da terminale/cmd):

   ```bash
   python main.py

##  Input consigliati per una simulazione rapida

Per una simulazione della durata di circa 5 minuti reali:
Inserire un valore di 300 come acceleratore temporale.

Per una simulazione della durata di circa 1 minuto reale:
Inserire un valore di 1500 come acceleratore temporale.