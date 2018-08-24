# AudioSync

Die folgenden Audiostreamingverfahren schreibe ich, um verschiedene Thesen meiner Bachelorarbeit praktisch zu untermauern. Dabei gibt es
verschiedene Lösungen einen Stream an verschiedene Clients zu Synchronisieren. 

## Vorrausetzung

Entweder man führt die folgenden Befehle aus, oder das ```install.sh``` - Skript.

* Installiere Pip:              ```sudo apt-get install python-pip libffi-dev libportaudio2```
* Installiere Sounddevice:      ```sudo pip install sounddevice soundfile ntplib```
* NTP:                          ```sudo apt-get install ntp```

## Befehle

* Server starten ```python server.py -h```
* Client starten ```python client.py -h```

## Verfahren 1 - v1:

Der Server öffnet die Audiodatei, statt aber die einzelnen gelesenen Chunks abzuspielen werden diese ein ein RTP Packet 
gepackt. Zusätzlich kommt der aktuelle Zeitstempel plus eine kleine Verzögerung. Wird das Packet empfangen, soll der
darin enthaltene Chunk erst abgespielt werden wenn die Zeit des Clients gleich der des Zeitstempels in dem Paket ist. 
Die Packete werden an einen Multicastchannel übertragen, dort kann jeder Client das selbe Packet empfangen.

Damit mehere Clients die chunks synchron abspielen, muss deren Zeit perfekt mit den anderen übereinstimmen.

## Verfahren 2 - v2:

Das Verfahren funktioniert etwas anders. Hier werden die Übertragungs- und Verarbeitungszeiten vom Server zum Client
gemessen und anhand den gewonnenen Werten die Audiopakete verzögert abgesendet. Ziel ist es, die Pakete
so abzuschicken, dass der Inhalt zum exakten gleichen Zeitpunkt abgespielt wird. Somit werden die Verzögerungen
ausgeglichen

* Server ```python server.py ../files/dlnm_.wav -s 192.168.178.60 -p 5555```
* Client ```python client.py -s 192.168.178.60 -p 5555 -v ```

