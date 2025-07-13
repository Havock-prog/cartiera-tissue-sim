class SimClock:
    def __init__(self, tick_interno, tick_visivo):
        self.tempo_simulato = 0
        self.tick_interno = tick_interno
        self.tick_visivo = tick_visivo

    def advance_internal(self):
        self.tempo_simulato += self.tick_interno

    def get_time(self):
        return self.tempo_simulato