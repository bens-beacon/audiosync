# AudioSync

Die folgenden Audiostreamingverfahren schreibe ich, um verschiedene Thesen meiner Bachelorarbeit praktisch zu untermauern. Dabei gibt es
verschiedene Lösungen einen Stream an verschiedene Clients zu Synchronisieren. 

## Vorrausetzung

* Installiere Pip:              ```sudo apt-get install python-pip```
* Installiere Sounddevice:      ```ssudo pip install sounddevice soundfile```
* NTP:                          ```sudo apt-get install ntp```

... statt Sounddevice ist auch PyAudio möglich... im "beta" Ordner.

## Befehle

* Server starten ```python server.py -h```
* Client starten ```python client.py -h```

## Verfahren 1 - v1:

Der Server öffnet die Audiodatei, statt aber die einzelnen gelesenen Chunks abzuspielen werden diese ein ein RTP Packet 
gepackt. Zusätzlich kommt der aktuelle Zeitstempel plus eine kleine Verzögerung. Wird das Packet empfangen, soll der
darin enthaltene Chunk erst abgespielt werden wenn die Zeit des Clients gleich der des Zeitstempels in dem Paket ist. Die Packete werden an einen Multicastchannel übertragen, dort kann jeder Client das selbe Packet empfangen.

Damit mehere Clients die chunks synchron abspielen, muss deren Zeit perfekt mit den anderen übereinstimmen. Hier könnte man PTPd verwenden.

### zu tun:

    * Verlorene Packete retten
    * Latenzen bestimmen,...

## Verfahren 2 - v2:

* Server ```python server.py ../files/dlnm_.wav -s 192.168.178.60 -p 5555```
* Client ```python client.py -s 192.168.178.60 -p 5555 -v ```




## Projektablauf

1. Test von Multicast
2. Bau einer RTP Bibliothek
3. Bau eine Abspielbibliothek
4. Bau Server und Client
5. Erste Tests
6. Synchronisation mit Protokollen- Server
7. Test, Messungen, Aussagen treffen

