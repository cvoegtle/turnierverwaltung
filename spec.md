# Turnierverwaltung
Ziel ist es ein Spieleturnier des Spieleclub Paderborns zu verwalten. Dabei treffen sich alle Spieler an einem Samstag und spielen vier Spiele, um den besten Spieler zu ermitteln. 

## Ablauf
Gespielt wird in vier Runden. Gespielt wird an Vierertischen, bzw. an Vierer- und Dreiertischen, sofern die Anzahl Spieler nicht durch 4 teilbar ist. In jeder Runde wird an allen Tischen das gleiche Spiel gespielt.

## Wertung am Tisch
Der Gewinner erhält 5 Punkte für den Sieg. Der zweite 3 Punkte, der Dritte 2 Punkte und der Vierte einen Punkt. Am Dreitertisch ist die Punkteverteilung 5, 3, 1. Bei Gleichstand werden die Punkte addiert und durch die Anzahl der Spieler die sich den Platz teilen geteilt. 

## Turnierwertung
Die Punkte jedes Spielers aus den vier Spielrunden werden addiert. Der Rang wird nach der Anzahl Punkte ermittelt. Der Spieler mit den meisten Punkten gewinnt.

# Business Objekte
## Spieler
ein Spieler hat einen Namen, eine eindeutige Nummer, seine Punkte aus den Spielen und eine gesamtpunktzahl 

## Spiel
hat einen Namen

## Tisch
ein Tisch hat 4 Plätze an denen Spieler platziert werden können. 

## Tischverteilung
Es gibt pro vier Spieler einen Tisch. Falls das nicht glatt aufgeht noch einen Tisch mehr
Für jede Spielrunde werden die Spieler auf die Turniertische verteilt.
Es gelten die folgenden Ziele bei der Verteilung, mit absteigender Wichtigkeit
Jeder Spieler soll möglichst gleich oft am 3er und am 4er Tisch spielen
Jeder Spieler soll einmal an jeder Position spielen
Jeder Spieler soll mit möglichst vielen anderen Spielern spielen

## Technik
Das Projekt soll in Python programmiert werden.
Es soll in Google Cloud Run deployed werden.
Es soll in den Google Datastore für die Persistenz nutzen
Die Business Logik soll unabhängig von der UI Technik implemtiert werden
Wir nutzen Flask für das UI.


