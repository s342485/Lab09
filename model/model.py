from database.regione_DAO import RegioneDAO
from database.tour_DAO import TourDAO
from database.attrazione_DAO import AttrazioneDAO

class Model:
    def __init__(self):
        self.tour_map = {} # Mappa ID tour -> oggetti Tour | chiave id
        self.attrazioni_map = {} # Mappa ID attrazione -> oggetti Attrazione

        self._pacchetto_ottimo = []  #lista di Tour che costituisce il miglior pacchetto trovato finora
        self._valore_ottimo: int = -1 #valore culturale del miglior pacchetto (inizialmente -1)

        # Caricamento
        self.load_tour()
        self.load_attrazioni()
        self.load_relazioni()

    @staticmethod
    def load_regioni():
        """ Restituisce tutte le regioni disponibili """
        return RegioneDAO.get_regioni()

    def load_tour(self):
        """ Carica tutti i tour in un dizionario [id, Tour]"""
        self.tour_map = TourDAO.get_tour()

        # Ogni tour avrà un set delle sue attrazioni
        for t in self.tour_map.values():
            t.attrazioni = set()

    def load_attrazioni(self):
        """ Carica tutte le attrazioni in un dizionario [id, Attrazione]"""
        self.attrazioni_map = AttrazioneDAO.get_attrazioni()

        for a in self.attrazioni_map.values():
            a.tours = set()

    def load_relazioni(self):
        """
            Interroga il database per ottenere tutte le relazioni fra tour e attrazioni e salvarle nelle strutture dati
            Collega tour <-> attrazioni.
            --> Ogni Tour ha un set di Attrazione.
            --> Ogni Attrazione ha un set di Tour.
        """
        relazioni = TourDAO.get_tour_attrazioni()

        for row in relazioni:  # row è un DICT {'id_tour': ..., 'id_attrazione': ...}
            id_tour = row["id_tour"]
            id_attr = row["id_attrazione"]

            tour = self.tour_map.get(id_tour)
            attr = self.attrazioni_map.get(id_attr)

            if tour is None or attr is None:
                continue

            tour.attrazioni.add(attr)
            attr.tours.add(tour)

    def genera_pacchetto(self, id_regione: str, max_giorni: int = None, max_budget: float = None):
        """
        Calcola il pacchetto turistico ottimale per una regione rispettando i vincoli di durata, budget e attrazioni uniche.
        :param id_regione: id della regione
        :param max_giorni: numero massimo di giorni (può essere None --> nessun limite)
        :param max_budget: costo massimo del pacchetto (può essere None --> nessun limite)

        :return: self._pacchetto_ottimo (una lista di oggetti Tour)
        :return: self._costo (il costo del pacchetto)
        :return: self._valore_ottimo (il valore culturale del pacchetto)
        """
        """
        Calcola il pacchetto turistico ottimale per una regione rispettando i vincoli:
        - nessuna attrazione duplicata
        - durata totale <= max_giorni
        - costo totale <= max_budget
        """


        if max_giorni not in ("", None):
            max_giorni = int(max_giorni)
        else:
            max_giorni = None

        if max_budget not in ("", None):
            max_budget = float(max_budget)
        else:
            max_budget = None

        # Reset risultati
        self._pacchetto_ottimo = []
        self._valore_ottimo = -1
        self._costo_ottimo = 0

        # Filtra i tour della regione selezionata
        lista_tour_regione = []
        for t in self.tour_map.values():
            if str(t.id_regione) == str(id_regione):
                lista_tour_regione.append(t)

        # avvia ricorsione
        self._ricorsione(lista_tour_regione,0,[],0,0,set(),max_giorni,max_budget)

        # Ritorna esattamente ciò che mi hai chiesto
        return self._pacchetto_ottimo, self._costo_ottimo, self._valore_ottimo

    def _ricorsione(self, lista_tour, index, pacchetto, giorni, costo, attr_usate, max_giorni, max_budget):

        # caso terminale
        if index == len(lista_tour):

            # valore culturale
            valore = 0
            for a in attr_usate:
                valore += a.valore_culturale

            # salva miglior pacchetto
            if valore > self._valore_ottimo:
                self._valore_ottimo = valore
                self._pacchetto_ottimo = pacchetto.copy()
                self._costo_ottimo = costo

            return

        tour = lista_tour[index]

        self._ricorsione(lista_tour, index + 1, pacchetto, giorni, costo,
                         attr_usate, max_giorni, max_budget)

        # controllo attrazioni duplicate
        duplicate = False
        for attr in tour.attrazioni:
            if attr in attr_usate:
                duplicate = True
                break

        if duplicate:
            # salto SOLO la scelta "prenderlo"
            return

        # controllo giorni
        nuovi_giorni = giorni + tour.durata_giorni
        if max_giorni is not None and nuovi_giorni > max_giorni:
            return

        # controllo budget
        nuovo_costo = costo + tour.costo
        if max_budget is not None and nuovo_costo > max_budget:
            return

        # prendo il tour
        pacchetto.append(tour)

        nuove_attr = set()
        for a in attr_usate:
            nuove_attr.add(a)
        for a in tour.attrazioni:
            nuove_attr.add(a)

        # ricorsione ramo "prendo il tour"
        self._ricorsione(lista_tour, index + 1, pacchetto,
                         nuovi_giorni, nuovo_costo, nuove_attr,
                         max_giorni, max_budget)

        # backtracking
        pacchetto.pop()